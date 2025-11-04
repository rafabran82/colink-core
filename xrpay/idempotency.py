import asyncio
import hashlib
import os
import time
from typing import Any, Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from xrpay.metrics import (
    IDEM_REQUESTS_TOTAL,
    IDEM_CACHE_MISS_TOTAL,
    IDEM_CACHE_HIT_TOTAL,
    IDEM_CONFLICT_TOTAL,
    IDEM_5XX_TOTAL,
    IDEM_LATENCY_SECONDS,
)

def _now() -> float:
    return time.time()

def _hash_bytes(b: Optional[bytes]) -> str:
    h = hashlib.sha256()
    h.update(b or b"")
    return h.hexdigest()

def _copy_safe_headers(resp: Response) -> Dict[str, str]:
    return {k: v for (k, v) in resp.headers.items()}

async def _extract_body_bytes(response: Response) -> bytes:
    body = getattr(response, "body", None)
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)

class AsyncMemoryStore:
    """Tiny async in-memory store with TTL."""
    def __init__(self) -> None:
        self._data: Dict[str, Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        now = _now()
        async with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            value, exp = item
            if exp is not None and exp <= now:
                try:
                    del self._data[key]
                except KeyError:
                    pass
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        exp = _now() + max(0, int(ttl_seconds))
        async with self._lock:
            self._data[key] = (value, exp)

# Optional Redis backend
try:
    from redis import asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

class AsyncRedisStore:
    """
    Redis-backed store: key -> packed tuple with TTL.
    Tuple: (body_bytes, status_code, media_type, headers_json, req_body_hash)
    """
    def __init__(self, url: str) -> None:
        if aioredis is None:
            raise RuntimeError("redis[async] client not installed")
        self._r = aioredis.from_url(url, decode_responses=False)

    async def get(self, key: str):
        raw = await self._r.get(key)
        if raw is None:
            return None
        parts = raw.split(b"\x1f", 4)
        if len(parts) != 5:
            return None
        body_bytes, sc_b, mt_b, hdrs_b, req_hash_b = parts
        try:
            sc = int(sc_b.decode())
        except Exception:
            sc = 200
        media_type = mt_b.decode() if mt_b else None
        import json
        try:
            headers_dict = json.loads(hdrs_b.decode() or "{}")
        except Exception:
            headers_dict = {}
        return (body_bytes, sc, media_type, headers_dict, req_hash_b.decode())

    async def set(self, key: str, value, ttl_seconds: int):
        (body_bytes, status_code, media_type, headers_dict, req_hash) = value
        import json
        mt_b   = (media_type or "").encode()
        sc_b   = str(status_code or 200).encode()
        hdrs_b = json.dumps(headers_dict or {}).encode()
        req_b  = (req_hash or "").encode()
        packed = b"\x1f".join([body_bytes or b"", sc_b, mt_b, hdrs_b, req_b])
        await self._r.setex(key, int(max(0, ttl_seconds)), packed)

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware with:
      - Tenant scoping (optional) via env XR_IDEMPOTENCY_TENANT_HEADER
      - Body-hash guard (409 on key reuse with different body)
      - No-cache on 5xx
      - Prometheus metrics
    """

    def __init__(
        self,
        app,
        *,
        store: AsyncMemoryStore | None = None,
        header_key: str = "Idempotency-Key",
        ttl_header: str = "Idempotency-TTL",
        default_ttl_seconds: int = 300,
    ) -> None:
        super().__init__(app)
        # backend
        if store is None:
            backend = os.getenv("XR_IDEMPOTENCY_BACKEND", "memory").lower()
            if backend == "redis":
                url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.store = AsyncRedisStore(url)
            else:
                self.store = AsyncMemoryStore()
        else:
            self.store = store

        self.header_key = header_key
        self.ttl_header = ttl_header
        self.default_ttl_seconds = int(default_ttl_seconds)
        self.tenant_header = os.getenv("XR_IDEMPOTENCY_TENANT_HEADER", "").strip() or None

    async def dispatch(self, request: Request, call_next):
        idem_key = request.headers.get(self.header_key)
        method = request.method.upper()
        path = request.url.path

        # Track requests (only those with idempotency key)
        if idem_key:
            IDEM_REQUESTS_TOTAL.labels(method=method, path=path).inc()

        # No key → passthrough with "none" cache label timing
        if not idem_key:
            start = _now()
            try:
                resp = await call_next(request)
                return resp
            finally:
                IDEM_LATENCY_SECONDS.labels(method=method, path=path, cache="none").observe(_now() - start)

        # TTL
        ttl_header_val = request.headers.get(self.ttl_header)
        try:
            ttl_seconds = int(ttl_header_val) if ttl_header_val is not None else self.default_ttl_seconds
        except ValueError:
            ttl_seconds = self.default_ttl_seconds

        # Request bytes + hash
        req_bytes = await request.body()
        req_hash = _hash_bytes(req_bytes)

        # Tenant prefix (optional)
        tenant_prefix = ""
        if self.tenant_header:
            tval = request.headers.get(self.tenant_header)
            if tval:
                tenant_prefix = f"{self.tenant_header}:{tval}::"

        cache_key = f"idemp::{tenant_prefix}{method}::{path}::{idem_key}"

        # Try cache
        start = _now()
        cached = await self.store.get(cache_key)
        if cached is not None:
            try:
                body_bytes, status_code, media_type, headers_dict, cached_req_hash = cached
            except ValueError:
                body_bytes = status_code = media_type = headers_dict = None
                cached_req_hash = None

            if cached_req_hash and cached_req_hash != req_hash:
                IDEM_CONFLICT_TOTAL.labels(method=method, path=path).inc()
                IDEM_LATENCY_SECONDS.labels(method=method, path=path, cache="hit").observe(_now() - start)
                return Response(
                    content=b'{"detail":"Idempotency key reused with different request body"}',
                    status_code=409,
                    media_type="application/json",
                    headers={"X-Idempotency-Conflict": "body-mismatch"},
                )

            headers_out = dict(headers_dict or {})
            headers_out["X-Idempotency-Cache"] = "hit"
            IDEM_CACHE_HIT_TOTAL.labels(method=method, path=path).inc()
            IDEM_LATENCY_SECONDS.labels(method=method, path=path, cache="hit").observe(_now() - start)
            return Response(
                content=body_bytes or b"",
                status_code=status_code or 200,
                media_type=media_type,
                headers=headers_out,
            )

        # MISS → call downstream
        response = await call_next(request)
        body_bytes = await _extract_body_bytes(response)
        media_type = getattr(response, "media_type", None)
        headers_dict = _copy_safe_headers(response)
        status_code = response.status_code

        # Never cache 5xx
        if 500 <= status_code <= 599:
            IDEM_5XX_TOTAL.labels(method=method, path=path).inc()
            IDEM_LATENCY_SECONDS.labels(method=method, path=path, cache="miss").observe(_now() - start)
            return Response(
                content=body_bytes,
                status_code=status_code,
                media_type=media_type,
                headers=headers_dict,
            )

        # Mark MISS
        IDEM_CACHE_MISS_TOTAL.labels(method=method, path=path).inc()
        headers_dict2 = dict(headers_dict)
        headers_dict2["X-Idempotency-Cache"] = "miss"

        new_resp = Response(
            content=body_bytes,
            status_code=status_code,
            media_type=media_type,
            headers=headers_dict2,
        )

        # Store
        await self.store.set(
            cache_key,
            (body_bytes, status_code, media_type, headers_dict, req_hash),
            ttl_seconds=ttl_seconds,
        )

        IDEM_LATENCY_SECONDS.labels(method=method, path=path, cache="miss").observe(_now() - start)
        return new_resp
