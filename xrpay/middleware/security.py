from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import time
from typing import Awaitable, Callable, Iterable, Optional, Union

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Types
SecretProvider = Callable[[str], Union[str, bytes, None, Awaitable[Union[str, bytes, None]]]]
KeyIdProvider  = Callable[[Request], Optional[str]]


def _default_secret_provider(key_id: str) -> Optional[bytes]:
    """
    Default demo secret provider: reads XRPAY_HMAC_SECRET from env.
    If multiple keys are desired, swap this for a KV/DB lookup by key_id.
    """
    secret = os.getenv("XRPAY_HMAC_SECRET", "devsecret")
    if isinstance(secret, str):
        return secret.encode("utf-8")
    return secret


def _default_key_id_provider(req: Request) -> Optional[str]:
    # Client should send X-XRPay-Key
    return req.headers.get("X-XRPay-Key")


class HMACMiddleware(BaseHTTPMiddleware):
    """
    Verifies HMAC headers on mutating requests.

    Expected headers:
      - X-XRPay-Key        : key identifier
      - X-XRPay-Timestamp  : unix seconds (int)
      - X-XRPay-Signature  : hex(HMAC_SHA256(secret, f"{ts}.{body}"))

    Message to sign:  "{ts}.{raw_body}"
    Comparison: case-insensitive, constant-time.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        secret_provider: Optional[SecretProvider] = None,
        key_id_provider: Optional[KeyIdProvider] = None,
        required_methods: Iterable[str] = ("POST", "PUT", "PATCH", "DELETE"),
        max_skew_seconds: int = 300,
        skip_paths: Iterable[str] = ("/healthz",),
    ) -> None:
        super().__init__(app)
        self.secret_provider = secret_provider or _default_secret_provider
        self.key_id_provider = key_id_provider or _default_key_id_provider
        self.required_methods = {m.upper() for m in required_methods}
        self.max_skew = int(max_skew_seconds)
        self.skip_paths = set(skip_paths)

    async def _get_secret(self, key_id: str) -> Optional[bytes]:
        # Support sync or async providers
        res = self.secret_provider(key_id)
        if asyncio.iscoroutine(res):
            res = await res  # await async secret resolution
        if res is None:
            return None
        if isinstance(res, str):
            return res.encode("utf-8")
        if isinstance(res, (bytes, bytearray)):
            return bytes(res)
        # Unknown type
        raise HTTPException(status_code=500, detail="Secret provider returned invalid type")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        if path in self.skip_paths:
            return await call_next(request)

        if method not in self.required_methods:
            # Skip HMAC for non-mutating methods
            return await call_next(request)

        key_id = self.key_id_provider(request)
        ts_hdr = request.headers.get("X-XRPay-Timestamp")
        sig_hdr = request.headers.get("X-XRPay-Signature")

        if not key_id or not ts_hdr or not sig_hdr:
            # === TEMP DEBUG: show exactly what headers the app is receiving ===
            try:
                print("HMAC DEBUG headers:", dict(request.headers))
            except Exception:
                pass
            raise HTTPException(status_code=401, detail="Missing HMAC headers")

        # Validate timestamp is int and within skew window
        try:
            ts = int(ts_hdr)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid HMAC timestamp")

        now = int(time.time())
        if abs(now - ts) > self.max_skew:
            raise HTTPException(status_code=401, detail="Timestamp outside allowed skew")

        # Read (and later replay) the request body
        raw = await request.body()

        # Starlette consumes the body when read; we must replay it for downstream handlers.
        async def _receive_once() -> dict:
            return {"type": "http.request", "body": raw, "more_body": False}
        request._receive = _receive_once  # type: ignore[attr-defined]

        # Build message: "ts.body"
        msg = f"{ts}.{raw.decode('utf-8', 'replace')}".encode("utf-8")

        # Fetch secret for key_id (supports async providers)
        secret = await self._get_secret(key_id)
        if not secret:
            raise HTTPException(status_code=401, detail="Unknown HMAC key")

        expected = hmac.new(secret, msg, hashlib.sha256).hexdigest().lower()
        provided = sig_hdr.strip().lower()

        if not hmac.compare_digest(provided, expected):
            raise HTTPException(status_code=401, detail="Invalid HMAC")

        # OK
        return await call_next(request)
