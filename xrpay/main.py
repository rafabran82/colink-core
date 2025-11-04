from fastapi import FastAPI, Request, Body
from starlette.responses import JSONResponse
import asyncio

from xrpay.middleware.security import HMACMiddleware
from xrpay.middleware.idempotency import IdempotencyMiddleware
from xrpay.liquidity.sim_provider import SimProvider
from xrpay.services.pricing import PricingEngine
from xrpay.services.webhook_dispatcher import WebhookDispatcher
from xrpay.repos import init_db, SQLIdemStore
from xrpay.routes.invoices import router as invoices_router
from xrpay.routes.payment_intents import router as intents_router
from xrpay.routes.hooks import router as hooks_router

async def secret_provider(_req: Request) -> str:
    return "dev_hmac_secret"

app = FastAPI(title="XRPay API", version="0.3.0")

# Init DB
init_db()

# Middlewares
app.add_middleware(HMACMiddleware, secret_provider=secret_provider)
app.add_middleware(IdempotencyMiddleware, store=SQLIdemStore())

# Services
_provider = SimProvider()
_pricing = PricingEngine(_provider)
_dispatcher = WebhookDispatcher()
_dispatcher_task = None

@app.on_event("startup")
async def on_startup():
    global _dispatcher_task
    _dispatcher_task = asyncio.create_task(_dispatcher.run())

@app.on_event("shutdown")
async def on_shutdown():
    global _dispatcher_task
    if _dispatcher_task:
        _dispatcher_task.cancel()

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

app.include_router(invoices_router)
app.include_router(intents_router)
app.include_router(hooks_router)
