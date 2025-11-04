from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import time, uuid

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
    if q.base.upper() != "XRP" or q.quote.upper() != "USD":
        raise HTTPException(status_code=422, detail="Only XRP/USD supported in demo")
    return {
        "id": uuid.uuid4().hex,
        "price": 0.6015,
        "fee_bps": 25,
        "impact_bps": q.slippageBps,
        "expiresAt": int(time.time()) + 30,
    }
