from fastapi import FastAPI, Request, Body
from starlette.responses import JSONResponse

from xrpay.middleware.security import HMACMiddleware
from xrpay.middleware.idempotency import IdempotencyMiddleware
from xrpay.liquidity.sim_provider import SimProvider
from xrpay.services.pricing import PricingEngine

from xrpay.routes.invoices import router as invoices_router
from xrpay.routes.payment_intents import router as payment_intents_router
from xrpay.routes.quotes import router as quotes_router
from xrpay.routes.hooks import router as hooks_router
from xrpay.routes.webhooks import router as webhooks_router
from xrpay.routes.debug import router as debug_router

class InMemoryIdemStore:
    def __init__(self): self._d = {}
    async def get(self, k): return self._d.get(k)
    async def set(self, k, v, ttl): self._d[k] = v

async def secret_provider(_req: Request) -> str:
    return "dev_hmac_secret"

app = FastAPI(title="XRPay API", version="0.3.0")

app.add_middleware(HMACMiddleware, secret_provider=secret_provider)
app.add_middleware(IdempotencyMiddleware, store=InMemoryIdemStore())

_provider = SimProvider()
_pricing = PricingEngine(_provider)

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/version")
async def version():
    return {"version": app.version}

# Routers
app.include_router(invoices_router)
app.include_router(payment_intents_router)
app.include_router(quotes_router)
app.include_router(hooks_router)
app.include_router(webhooks_router)
app.include_router(debug_router)
