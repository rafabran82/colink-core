import asyncio
import hashlib
import time
from typing import Any, Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def _now() -> float:
    return time.time()


def _hash_bytes(b: Optional[bytes]) -> str:
    h = hashlib.sha256()
    h.update(b or b"")
    return h.hexdigest()


def _copy_safe_headers(resp: Response) -> Dict[str, str]:
    # Copy response headers into a plain dict (case-insensitive on output is fine)
    return {k: v for (k, v) in resp.headers.items()}


async def _extract_body_bytes(response: Response) -> bytes:
    """
    Prefer response.body when present (e.g., JSONResponse/PlainTextResponse),
    otherwise drain body_iterator.
    """
    body = getattr(response, "body", None)
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)


class AsyncMemoryStore:
    """
    Tiny async in-memory store with TTL.
    Values are stored as: key -> (value, expires_at)
    Value for idempotency is a tuple:
      (body_bytes, status_code, media_type, headers_dict, req_body_hash)
    """

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
                # expired, delete and return None
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


class IdempotencyMiddleware(BaseHTTPMiddleware):
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

    async def dispatch(self, request: Request, call_next):
        # If no key, passthrough
        idem_key = request.headers.get(self.header_key)
        if not idem_key:
            return await call_next(request)

        # Build cache key (include method + path)
        method = request.method.upper()
        path = request.url.path
        cache_key = f"idemp::{method}::{path}::{idem_key}"

        # TTL from header (optional)
        ttl_header_val = request.headers.get(self.ttl_header)
        try:
            ttl_seconds = int(ttl_header_val) if ttl_header_val is not None else self.default_ttl_seconds
        except ValueError:
            ttl_seconds = self.default_ttl_seconds

        # Read request body (Starlette caches it; safe to read here)
        req_bytes = await request.body()
        req_hash = _hash_bytes(req_bytes)

        # Check cache first
        cached = await self.store.get(cache_key)
        if cached is not None:
            try:
                body_bytes, status_code, media_type, headers_dict, cached_req_hash = cached
            except ValueError:
                # Backward-compat: older 4-tuple entries => treat as conflict-safe MISS
                body_bytes = status_code = media_type = headers_dict = None
                cached_req_hash = None

            if cached_req_hash and cached_req_hash != req_hash:
                # 409 Conflict: same idempotency key, *different* request body
                return Response(
                    content=b'{"detail":"Idempotency key reused with different request body"}',
                    status_code=409,
                    media_type="application/json",
                    headers={"X-Idempotency-Conflict": "body-mismatch"},
                )

            headers_out = dict(headers_dict or {})
            headers_out["X-Idempotency-Cache"] = "hit"
            return Response(
                content=body_bytes or b"",
                status_code=status_code or 200,
                media_type=media_type,
                headers=headers_out,
            )

        # MISS: call downstream, capture & cache
        response = await call_next(request)

        body_bytes = await _extract_body_bytes(response)
        media_type = getattr(response, "media_type", None)
        headers_dict = _copy_safe_headers(response)
        status_code = response.status_code

        # Add visibility header
        headers_dict2 = dict(headers_dict)
        headers_dict2["X-Idempotency-Cache"] = "miss"

        new_resp = Response(
            content=body_bytes,
            status_code=status_code,
            media_type=media_type,
            headers=headers_dict2,
        )

        # Cache with the request body hash
        await self.store.set(
            cache_key,
            (body_bytes, status_code, media_type, headers_dict, req_hash),
            ttl_seconds=ttl_seconds,
        )
        return new_resp

