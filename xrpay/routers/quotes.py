from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class QuoteIn(BaseModel):
    base: str
    quote: str
    side: str = Field(pattern="^(BUY|SELL)$")
    amount: str
    slippageBps: int = Field(ge=0, le=10_000)

class QuoteOut(BaseModel):
    id: str
    price: float
    fee_bps: int
    impact_bps: int
    expiresAt: int

@router.post("/quotes", response_model=QuoteOut)
async def create_quote(q: QuoteIn):
    # super simple demo math; replace with real pricing later
    base = q.base.upper()
    quote = q.quote.upper()
    if base != "XRP" or quote != "USD":
        raise HTTPException(status_code=422, detail="Only XRP/USD supported in demo")

    import time, uuid
    price = 0.6015
    fee_bps = 25
    impact_bps = q.slippageBps
    return {
        "id": uuid.uuid4().hex,
        "price": price,
        "fee_bps": fee_bps,
        "impact_bps": impact_bps,
        "expiresAt": int(time.time()) + 30,
    }
