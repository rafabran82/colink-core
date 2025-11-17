from fastapi import FastAPI

from routes.debug import router as debug_router

# Routers
from routes.sim import router as sim_router

app = FastAPI(title="COLINK Core")


def include_prefix_smart(app, router, expected_prefix: str):
    # If the router already has a prefix, just include it as-is.
    # Otherwise, mount it at the expected_prefix.
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
    from routes.orderbook import router as orderbook_router  # type: ignore
except Exception:
    orderbook_router = None

if orderbook_router is not None:
    include_prefix_smart(app, orderbook_router, "/orderbook")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

