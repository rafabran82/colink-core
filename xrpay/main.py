from __future__ import annotations

from fastapi import FastAPI
import os
try:
    _XR_TTL = int(os.getenv("XR_IDEMPOTENCY_TTL", "300"))
except ValueError:
    _XR_TTL = 300
from xrpay.idempotency import IdempotencyMiddleware, AsyncMemoryStore

app = FastAPI(
app.add_middleware(IdempotencyMiddleware, store=AsyncMemoryStore(), default_ttl_seconds=_XR_TTL)
    title="XRPay",
    version="0.1.0",
    contact={"name": "COLINK / XRPay"},
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

# --- HMAC first (no idempotency for now so we can debug cleanly) ---
from xrpay.middleware.security import HMACMiddleware
app.add_middleware(HMACMiddleware)

# --- Test echo route so we can see exactly what FastAPI receives ---
from xrpay.routers.test import router as _test_router
app.include_router(_test_router)

# (We will add real routers + IdempotencyMiddleware once HMAC is confirmed)
# === Idempotency (restore after HMAC is confirmed) ===
from xrpay.middleware.idempotency import IdempotencyMiddleware

class _MemoryStore:
    def __init__(self):
        from threading import RLock
        self._d = {}
        self._lock = RLock()
    def get(self, key):
        with self._lock: return self._d.get(key)
    def set(self, key, value, ttl_seconds=600):
        # (Simple demo: ignore TTL or store (value, expiry) as needed)
        with self._lock: self._d[key] = value

_idem_store = _MemoryStore()
# --- Real routers ---
from xrpay.routers.quotes import router as quotes_router
app.include_router(quotes_router)
# --- XRPay routers ---
try:
    from xrpay.routers.test import router as test_router
    app.include_router(test_router)
    print("[xrpay.main] Included: /_echo")
except Exception as e:
    print(f"[xrpay.main] Skipped /_echo: {e}")

try:
    from xrpay.routers.quotes import router as quotes_router
    app.include_router(quotes_router)
    print("[xrpay.main] Included: /quotes")
except Exception as e:
    print(f"[xrpay.main] Skipped /quotes: {e}")
# --- XRPay idempotency store (awaitable) ---
from xrpay.middleware.idem_store import AsyncMemoryStore
_idem_store = AsyncMemoryStore()

# Attach idempotency AFTER HMAC so the verified raw body is available
from xrpay.middleware.idempotency import IdempotencyMiddleware




# --- XRPay debug: middleware snapshot ---
def _mw_snapshot():
    try:
        stack = [mw.cls.__name__ for mw in app.user_middleware]
        return {'middleware': stack}
    except Exception as e:
        return {'error': str(e)}

