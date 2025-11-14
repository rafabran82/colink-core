from fastapi import FastAPI
from fastapi.routing import APIRouter

from routes.debug import router as debug_router
from routes.sim import router as sim_router

# === Import dashboard API (Phase 3 pools + swaps) ===
import dashboard_api

app = FastAPI(title="COLINK Core")

def include_prefix_smart(app, router, expected_prefix: str):
    rp = getattr(router, "prefix", "") or ""
    if rp:
        app.include_router(router)
    else:
        app.include_router(router, prefix=expected_prefix)

# Always-on routers
include_prefix_smart(app, sim_router, "/sim")
include_prefix_smart(app, debug_router, "/debug")

# Optional XRPL routes
try:
    from routes.orderbook import router as orderbook_router
except Exception:
    orderbook_router = None

if orderbook_router is not None:
    include_prefix_smart(app, orderbook_router, "/orderbook")

# === Mount dashboard API under /api ===
# dashboard_api.app includes:
#   /api/sim/meta
#   /api/pools/state
#   /api/swaps/recent
app.mount("/", dashboard_api.app)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
