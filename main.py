from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

import os

from xrpay.idempotency import IdempotencyMiddleware, AsyncMemoryStore
# Routers
from xrpay.routes.quotes import router as quotes_router
from xrpay.routes.debug import router as debug_router
from xrpay.routes.payment_intents import router as pi_router
from xrpay.routes_core import router as core_router

# Prometheus
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# TTL knob (idempotency)
try:
    _XR_TTL = int(os.getenv("XR_IDEMPOTENCY_TTL", "300"))
except ValueError:
    _XR_TTL = 300

app = FastAPI(title="COLINK Core API", version="0.3.0")

# Idempotency before CORS
app.add_middleware(
    IdempotencyMiddleware,
    store=AsyncMemoryStore(),
    default_ttl_seconds=_XR_TTL,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Mount routes
app.include_router(quotes_router)
app.include_router(debug_router)
app.include_router(pi_router)
app.include_router(core_router)
