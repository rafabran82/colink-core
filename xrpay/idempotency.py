from __future__ import annotations
import asyncio
import time
from typing import Any, Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

class AsyncMemoryStore:
    def __init__(self, default_ttl_seconds: int = 300):
        self._data: Dict[str, Tuple[Any, float]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._default_ttl = default_ttl_seconds
        self._gc_lock = asyncio.Lock()
    def _now(self) -> float: return time.time()
    async def get(self, key: str) -> Optional[Any]:
        item = self._data.get(key)
        if not item: return None
        value, expires_at = item
        if self._now() >= expires_at:
            self._data.pop(key, None)
            return None
        return value
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._data[key] = (value, self._now() + ttl)
    async def delete(self, key: str) -> None:
        self._data.pop(key, None)
    async def get_lock(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock
    async def gc(self) -> int:
        removed = 0
        async with self._gc_lock:
            now = self._now()
            for k in list(self._data.keys()):
                _, exp = self._data.get(k, (None, 0))
                if now >= exp:
                    self._data.pop(k, None)
                    removed += 1
        return removed

SAFE_HEADER_PREFIXES = ("content-type", "cache-control")
IDEMPOTENCY_HEADER = "idempotency-key"
IDEMPOTENCY_TTL_HEADER = "idempotency-ttl"

def _cacheable_method(method: str) -> bool:
    return method in ("POST", "PUT", "PATCH")

def _build_cache_key(request: Request, idempotency_key: str) -> str:
    return f"idemp::{request.method}::{request.url.path}::{idempotency_key}"

def _copy_safe_headers(response: Response) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in response.headers.items():
        if k.lower().startswith(SAFE_HEADER_PREFIXES):
            out[k] = v
    return out

async def _extract_body_bytes(response: Response) -> bytes:
    body = getattr(response, "body", None)
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)

class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, store: AsyncMemoryStore, default_ttl_seconds: int = 300) -> None:
        super().__init__(app)
        self.store = store
        self.default_ttl_seconds = default_ttl_seconds

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        if not _cacheable_method(method):
            return await call_next(request)

        idemp_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idemp_key:
            return await call_next(request)

        ttl_hdr = request.headers.get(IDEMPOTENCY_TTL_HEADER)
        ttl_seconds: Optional[int] = None
        if ttl_hdr:
            try:
                ttl_seconds = max(1, int(ttl_hdr))
            except ValueError:
                ttl_seconds = None

        cache_key = _build_cache_key(request, idemp_key)

        cached = await self.store.get(cache_key)
        if cached is not None:
            body_bytes, status_code, media_type, headers_dict = cached
            headers_out = dict(headers_dict)
            headers_out["X-Idempotency-Cache"] = "hit"
            print(f"[Idempotency] HIT {cache_key}")
            return Response(content=body_bytes, status_code=status_code, media_type=media_type, headers=headers_out)

        lock = await self.store.get_lock(cache_key)
        async with lock:
            cached = await self.store.get(cache_key)
            if cached is not None:
                body_bytes, status_code, media_type, headers_dict = cached
                headers_out = dict(headers_dict)
                headers_out["X-Idempotency-Cache"] = "hit"
                print(f"[Idempotency] HIT(after-lock) {cache_key}")
                return Response(content=body_bytes, status_code=status_code, media_type=media_type, headers=headers_out)

            response = await call_next(request)
            body_bytes = await _extract_body_bytes(response)
            media_type = getattr(response, "media_type", None)
            headers_dict = _copy_safe_headers(response)
            status_code = response.status_code

            headers_out = dict(headers_dict)
            headers_out["X-Idempotency-Cache"] = "miss"

            new_resp = Response(content=body_bytes, status_code=status_code, media_type=media_type, headers=headers_out)

            await self.store.set(
                cache_key,
                (body_bytes, status_code, media_type, headers_dict),
                ttl_seconds=ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds,
            )
            print(f"[Idempotency] MISS {cache_key} cached for {ttl_seconds or self.default_ttl_seconds}s")

            return new_resp