from fastapi import FastAPI, Request, Body
from starlette.responses import JSONResponse

from xrpay.middleware.security import HMACMiddleware
from xrpay.middleware.idempotency import IdempotencyMiddleware
from xrpay.liquidity.sim_provider import SimProvider
from xrpay.services.pricing import PricingEngine

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

@app.post("/quotes")
async def make_quote(payload: dict = Body(...)):
    data = await _pricing.quote(payload)
    return JSONResponse(data)
