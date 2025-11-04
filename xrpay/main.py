from fastapi import FastAPI, Body
from starlette.responses import JSONResponse

from xrpay.middleware.security import HMACMiddleware
from xrpay.middleware.idempotency import IdempotencyMiddleware
from xrpay.liquidity.sim_provider import SimProvider
from xrpay.services.pricing import PricingEngine

from xrpay.routes.hooks import router as hooks_router
from xrpay.routes.quotes import router as quotes_router
from xrpay.routes.payment_intents import router as payment_intents_router
from xrpay.routes.webhooks import router as webhooks_router
from xrpay.routes.debug import router as debug_router
from xrpay.routes.invoices import router as invoices_router

# DB bootstrap safety (even if import order changes)
from xrpay.db import Base, engine

class InMemoryIdemStore:
    def __init__(self): self._d = {}
    async def get(self, k): return self._d.get(k)
    async def set(self, k, v, ttl): self._d[k] = v

async def secret_provider(_req) -> str:
    return "dev_hmac_secret"

app = FastAPI(title="XRPay API", version="0.3.1")

# Force tables on startup in case prior create_all missed them
@app.on_event("startup")
def _ensure_db():
    Base.metadata.create_all(bind=engine)

app.add_middleware(HMACMiddleware, secret_provider=secret_provider)
app.add_middleware(IdempotencyMiddleware, store=InMemoryIdemStore())

_provider = SimProvider()
_pricing  = PricingEngine(_provider)

@app.get("/healthz")
async def healthz(): return {"ok": True}

@app.get("/version")
async def version(): return {"version": app.version}

# keep minimal passthrough for backward-compat
@app.post("/quotes")
async def make_quote(payload: dict = Body(...)):
    data = await _pricing.quote(payload)
    return JSONResponse(data)

# Routers
app.include_router(invoices_router)
app.include_router(hooks_router)
app.include_router(quotes_router)
app.include_router(payment_intents_router)
app.include_router(webhooks_router)
app.include_router(debug_router)
from fastapi import Body
@app.get("/__who/pricing")
def __who_pricing():
    import xrpay.services.pricing as p
    info = {
        "module": getattr(p, "__file__", None),
        "class_has_quote": hasattr(p.PricingEngine, "quote"),
        "instance_type": str(type(globals().get("_pricing", None))),
        "instance_has_quote": hasattr(globals().get("_pricing", None), "quote"),
    }
    return info
from fastapi import Body
@app.get("/__who/pricing")
def __who_pricing():
    import xrpay.services.pricing as p
    info = {
        "module": getattr(p, "__file__", None),
        "class_has_quote": hasattr(p.PricingEngine, "quote"),
        "instance_type": str(type(globals().get("_pricing", None))),
        "instance_has_quote": hasattr(globals().get("_pricing", None), "quote"),
    }
    return info

