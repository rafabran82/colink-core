from __future__ import annotations
import time
from asyncio import Lock

class AsyncMemoryStore:
    """
    Minimal awaitable store for IdempotencyMiddleware.
    NOTE: TTL is optional; value structure can be adapted if middleware expects raw response.
    """
    def __init__(self):
        self._d = {}
        self._ttl = {}
        self._lock = Lock()

    async def get(self, key: str):
        now = time.time()
        async with self._lock:
            exp = self._ttl.get(key)
            if exp is not None and exp < now:
                # expired
                self._d.pop(key, None)
                self._ttl.pop(key, None)
                return None
            return self._d.get(key)

    async def set(self, key: str, value, ttl_seconds: int = 600):
        async with self._lock:
            self._d[key] = value
            if ttl_seconds:
                self._ttl[key] = time.time() + ttl_seconds
            else:
                self._ttl.pop(key, None)
