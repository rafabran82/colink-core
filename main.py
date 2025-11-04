from fastapi import FastAPI
import inspect
import os
from xrpay.routes_core import router as core_router
from xrpay.idempotency import IdempotencyMiddleware, AsyncMemoryStore
from fastapi.middleware.cors import CORSMiddleware

from routes.orderbook import router as orderbook_router
from routes.trade import router as trade_router
from routes.debug import router as debug_router
from routes.paper_admin import router as paper_admin_router
from routes.paper_portfolio import router as paper_portfolio_router

app = FastAPI(title="COLINK Core API", version="0.3.0")


# Optional API prefix (e.g., /api or /v1). Empty by default.
XR_API_PREFIX = os.getenv('XR_API_PREFIX', '').strip()
app.include_router(core_router, prefix=XR_API_PREFIX)
# CORS (relaxed for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

# Routers
app.include_router(orderbook_router)
app.include_router(trade_router)
app.include_router(debug_router)
app.include_router(paper_admin_router)
app.include_router(paper_portfolio_router)



@app.on_event('startup')
async def _log_routes():
    try:
        print('== XRPay routes ==')
        for r in app.router.routes:
            m = getattr(r, 'methods', None)
            p = getattr(r, 'path', None)
            if m and p:
                print(f'  {sorted(m)} {p}')
    except Exception as e:
        print('Route log error:', e)

@app.on_event('startup')
async def _log_mw():
    try:
        import xrpay.idempotency as _idm
        print('== XRPay middleware (outermost first) ==')
        for mw in app.user_middleware:
            print('  -', mw.cls.__name__)
        print('Idempotency module file:', getattr(_idm, '__file__', '-'))
    except Exception as e:
        print('Middleware log error:', e)







