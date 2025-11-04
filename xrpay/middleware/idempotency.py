from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Optional, Tuple, Dict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

IDEMPOTENCY_HEADER = "Idempotency-Key"

class InMemoryIdempotencyStore:
    """
    Super-simple in-memory store with TTL. Good enough for dev/testing.
    Keys: (idempotency_key) -> (status:int, headers:list[tuple[str,str]], body:bytes, expires_at:int)
    """
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._data: Dict[str, Tuple[int, list[tuple[str, str]], bytes, int]] = {}
        self._lock = asyncio.Lock()

    async def _purge(self) -> None:
        now = int(time.time())
        dead = [k for k, (_, _, _, exp) in self._data.items() if exp <= now]
        for k in dead:
            self._data.pop(k, None)

    async def get(self, key: str) -> Optional[Tuple[int, list[tuple[str, str]], bytes]]:
        async with self._lock:
            await self._purge()
            entry = self._data.get(key)
            if not entry:
                return None
            status, headers, body, _ = entry
            return status, headers, body

    async def set(self, key: str, status: int, headers: list[tuple[str, str]], body: bytes) -> None:
        async with self._lock:
            await self._purge()
            self._data[key] = (status, headers, body, int(time.time()) + self.ttl)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Caches the first successful response for requests carrying an Idempotency-Key.
    On duplicate requests with the same key, returns the cached response.
    Intended for POST/PUT/PATCH that create/modify resources.

    Notes:
      - For dev it uses a provided store (InMemoryIdempotencyStore by default).
      - Production should use a shared external store (redis/sql/etc).
    """

    def __init__(self, app: ASGIApp, *, store: InMemoryIdempotencyStore, methods=("POST","PUT","PATCH")) -> None:
        super().__init__(app)
        self.store = store
        self.methods = {m.upper() for m in methods}

    async def dispatch(self, request: Request, call_next):
        if request.method.upper() not in self.methods:
            return await call_next(request)

        key = request.headers.get(IDEMPOTENCY_HEADER)
        if not key:
            # No key, just pass through
            return await call_next(request)

        # If we already have a cached response, replay it
        cached = await self.store.get(key)
        if cached:
            status, headers, body = cached
            async def _send(send):
                await send({"type":"http.response.start","status":status,"headers":headers})
                await send({"type":"http.response.body","body":body,"more_body":False})
            return _SendResponse(_send)

        # Capture downstream response
        recorder = _ResponseRecorder()
        response = await call_next(request)
        await recorder.capture(response)

        # Cache only if status is 2xx
        if 200 <= recorder.status < 300:
            await self.store.set(key, recorder.status, recorder.headers, recorder.body)

        # Return the recorded response to client
        async def _send_passthrough(send):
            await send({"type":"http.response.start","status":recorder.status,"headers":recorder.headers})
            await send({"type":"http.response.body","body":recorder.body,"more_body":False})
        return _SendResponse(_send_passthrough)


class _SendResponse:
    """ASGI response wrapper to push a prebuilt response."""
    def __init__(self, sender):
        self._sender = sender
    async def __call__(self, scope, receive, send):
        await self._sender(send)


class _ResponseRecorder:
    """Collects status/headers/body from a Starlette Response."""
    def __init__(self):
        self.status = 200
        self.headers: list[tuple[str,str]] = []
        self.body: bytes = b""

    async def capture(self, response):
        # Starlette Response has background and body_iterator; easiest is to call .__call__ with a custom send
        async def send(message):
            if message["type"] == "http.response.start":
                self.status = message["status"]
                # headers are in raw byte tuples
                hdrs = message.get("headers") or []
                self.headers = [(k.decode("latin-1"), v.decode("latin-1")) for k,v in hdrs]
            elif message["type"] == "http.response.body":
                self.body += message.get("body", b"")
        await response(None, None, send)
