from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
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
app.add_middleware(IdempotencyMiddleware, store=_idem_store)
