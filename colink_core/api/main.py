from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from top-level routes/ folder
from routes import (
    sim,
    status,
    orderbook,
    trustline,
    dex,
    offers,
    report,
    trade,
    paper_admin,
    paper_portfolio,
    debug,
)

app = FastAPI(title="COLINK API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(sim.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(orderbook.router, prefix="/api")
app.include_router(trustline.router, prefix="/api")
app.include_router(dex.router, prefix="/api")
app.include_router(offers.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(trade.router, prefix="/api")
app.include_router(paper_admin.router, prefix="/api")
app.include_router(paper_portfolio.router, prefix="/api")
app.include_router(debug.router, prefix="/api")
