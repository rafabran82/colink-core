from fastapi import FastAPI
from routes.status import router as status_router
from routes.offers import router as offers_router
from routes.orderbook import router as orderbook_router
from routes.trade import router as trade_router  # NEW

app = FastAPI(title="COLINK Core", version="0.1")

app.include_router(status_router)
app.include_router(offers_router)
app.include_router(orderbook_router)
app.include_router(trade_router)  # NEW

@app.get("/healthz")
def healthz():
    return {"ok": True}
