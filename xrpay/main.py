from __future__ import annotations

from fastapi import FastAPI

# Optional router imports (won't crash app if a module is missing)
def _try_include_router(app: FastAPI, dotted: str, name: str) -> None:
    try:
        mod_path, attr = dotted.rsplit(":", 1)
        mod = __import__(mod_path, fromlist=[attr])
        router = getattr(mod, attr)
        app.include_router(router)
        print(f"[xrpay.main] Included router: {name} ({dotted})")
    except Exception as e:
        print(f"[xrpay.main] Skipped router {name}: {e}")

app = FastAPI(
    title="XRPay",
    version="0.1.0",
    contact={"name": "COLINK / XRPay"},
)

# Health first so we can always probe the service
@app.get("/healthz")
def healthz():
    return {"ok": True}

# === XRPay middleware begin ===
# Authenticate first (ensures raw body is intact), then idempotency
from xrpay.middleware.security import HMACMiddleware
from xrpay.middleware.idempotency import IdempotencyMiddleware

app.add_middleware(HMACMiddleware)
app.add_middleware(IdempotencyMiddleware)
# === XRPay middleware end ===

# Routers (add/rename these dotted paths to match your project layout)
# Examples below try common locations; they fail "soft" if not present.
_try_include_router(app, "xrpay.routers.quotes:router", "quotes")
_try_include_router(app, "xrpay.routers.invoices:router", "invoices")
_try_include_router(app, "xrpay.routers.payments:router", "payments")
_try_include_router(app, "xrpay.api.quotes:router", "quotes(api)")
_try_include_router(app, "xrpay.api.invoices:router", "invoices(api)")
_try_include_router(app, "xrpay.api.payments:router", "payments(api)")
