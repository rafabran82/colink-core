from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.debug import router as debug_router
from routes.orderbook import router as orderbook_router
from routes.paper_admin import router as paper_admin_router
from routes.paper_portfolio import router as paper_portfolio_router
from routes.trade import router as trade_router

app = FastAPI(title="COLINK Core API", version="0.3.0")

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
