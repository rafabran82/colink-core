import asyncio
import hashlib
import json
import os
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
    # Copy response headers into a plain dict
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


# Optional Redis backend (cluster-safe)
try:
    from redis import asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None


class AsyncRedisStore:
    """
    Redis-backed store: key -> packed tuple, with TTL.
    Tuple fields: (body_bytes, status_code, media_type, headers_dict, req_body_hash)
    We avoid pickle; pack fields with a simple delimiter.
    """

    SEP = b"\x1f"  # unit-separator byte

    def __init__(self, url: str) -> None:
        if aioredis is None:
            raise RuntimeError("redis[async] client not installed")
        self._r = aioredis.from_url(url, decode_responses=False)

    async def get(self, key: str):
        raw = await self._r.get(key)
        if raw is None:
            return None
        parts = raw.split(self.SEP, 5)
        if len(parts) != 5:
            return None
        body_bytes, sc_b, mt_b, hdrs_b, req_hash_b = parts
        try:
            status_code = int(sc_b.decode() or "200")
        except Exception:
            status_code = 200
        media_type = mt_b.decode() if mt_b else None
        try:
            headers_dict = json.loads(hdrs_b.decode() or "{}")
        except Exception:
            headers_dict = {}
        return (body_bytes, status_code, media_type, headers_dict, req_hash_b.decode())

    async def set(self, key: str, value, ttl_seconds: int):
        (body_bytes, status_code, media_type, headers_dict, req_hash) = value
        mt_b = (media_type or "").encode()
        sc_b = str(status_code or 200).encode()
        hdrs_b = json.dumps(headers_dict or {}).encode()
        req_b = (req_hash or "").encode()
        packed = self.SEP.join([body_bytes or b"", sc_b, mt_b, hdrs_b, req_b])
        await self._r.setex(key, int(max(0, ttl_seconds)), packed)


class InflightRegistry:
    """
    Deduplicate concurrent requests for the same (method, path, key).
    Leader computes the response, followers await the result.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._futs: Dict[str, asyncio.Future] = {}

    async def acquire(self, key: str) -> Tuple[bool, asyncio.Future]:
        async with self._lock:
            fut = self._futs.get(key)
            if fut is None or fut.done():
                fut = asyncio.get_event_loop().create_future()
                self._futs[key] = fut
                return True, fut  # leader
            return False, fut   # follower

    async def resolve(self, key: str, result: Any) -> None:
        async with self._lock:
            fut = self._futs.get(key)
            if fut and not fut.done():
                fut.set_result(result)

    async def fail(self, key: str, exc: BaseException) -> None:
        async with self._lock:
            fut = self._futs.get(key)
            if fut and not fut.done():
                fut.set_exception(exc)

    async def clear(self, key: str) -> None:
        async with self._lock:
            self._futs.pop(key, None)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware:

    - Uses header "Idempotency-Key" (configurable) + method + path to build a cache key.
    - Optional per-request TTL header "Idempotency-TTL" (defaults to middleware default).
    - On HIT: recomputes *request body hash* and compares to cached; mismatch => 409.
    - On MISS: calls downstream, captures the response body once, stores it along with
      the request body hash, returns the response, and adds `X-Idempotency-Cache: miss`.
    - Single-flight: concurrent calls with same key will await the leader's result.
    """

    def __init__(
        self,
        app,
        *,
        store: Optional[Any] = None,
        header_key: str = "Idempotency-Key",
        ttl_header: str = "Idempotency-TTL",
        default_ttl_seconds: int = 300,
    ) -> None:
        super().__init__(app)
        # Choose backend if not provided
        if store is None:
            backend = os.getenv("XR_IDEMPOTENCY_BACKEND", "memory").lower()
            if backend == "redis":
                url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                store = AsyncRedisStore(url)
            else:
                store = AsyncMemoryStore()

        self.store = store
        self.header_key = header_key
        self.ttl_header = ttl_header
        self.default_ttl_seconds = int(default_ttl_seconds)
        self._inflight = InflightRegistry()

    async def dispatch(self, request: Request, call_next):
        # If no key, passthrough
        idem_key = request.headers.get(self.header_key)
        if not idem_key:
            return await call_next(request)

        # Build cache key
        method = request.method.upper()
        path = request.url.path
        cache_key = f"idemp::{method}::{path}::{idem_key}"

        # TTL from header (optional)
        ttl_header_val = request.headers.get(self.ttl_header)
        try:
            ttl_seconds = int(ttl_header_val) if ttl_header_val is not None else self.default_ttl_seconds
        except ValueError:
            ttl_seconds = self.default_ttl_seconds

        # Read request body (Starlette caches; safe to read here)
        req_bytes = await request.body()
        req_hash = _hash_bytes(req_bytes)

        # First: check cache for immediate HIT
        cached = await self.store.get(cache_key)
        if cached is not None:
            body_bytes, status_code, media_type, headers_dict, cached_req_hash = cached
            if cached_req_hash and cached_req_hash != req_hash:
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

        # No cache yet: try single-flight
        is_leader, fut = await self._inflight.acquire(cache_key)
        if not is_leader:
            # Follower waits for leader
            try:
                await fut
            finally:
                pass
            # After leader finishes, behave like a HIT path
            cached2 = await self.store.get(cache_key)
            if cached2 is None:
                # Leader failed in some way; proceed downstream (rare)
                return await call_next(request)
            body_bytes, status_code, media_type, headers_dict, cached_req_hash = cached2
            if cached_req_hash and cached_req_hash != req_hash:
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

        # Leader: compute, cache, resolve followers
        try:
            response = await call_next(request)
            body_bytes = await _extract_body_bytes(response)
            media_type = getattr(response, "media_type", None)
            headers_dict = _copy_safe_headers(response)
            status_code = response.status_code

            headers_dict2 = dict(headers_dict)
            headers_dict2["X-Idempotency-Cache"] = "miss"

            # Cache with request hash
            await self.store.set(
                cache_key,
                (body_bytes, status_code, media_type, headers_dict, req_hash),
                ttl_seconds=ttl_seconds,
            )

            new_resp = Response(
                content=body_bytes,
                status_code=status_code,
                media_type=media_type,
                headers=headers_dict2,
            )

            await self._inflight.resolve(cache_key, True)
            return new_resp
        except BaseException as e:
            await self._inflight.fail(cache_key, e)
            raise
        finally:
            await self._inflight.clear(cache_key)
