from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..db import session_scope
from ..models import Quote
from ..services.pricing import pricing_engine   # existing singleton created in main.py

router = APIRouter(prefix="/quotes", tags=["quotes"])

class CreateQuoteIn(BaseModel):
    base: str
    quote: str
    side: str
    amount: float
    slippageBps: int | None = Field(default=None, alias="slippageBps")

class CreateQuoteOut(BaseModel):
    id: int
    price: float
    fee_bps: int = Field(..., alias="fee_bps")
    impact_bps: int = Field(..., alias="impact_bps")
    expiresAt: int

@router.post("", response_model=CreateQuoteOut)
async def create_quote(payload: CreateQuoteIn):
    # get a price from the engine
    data = await pricing_engine.quote({
        "base": payload.base,
        "quote": payload.quote,
        "side": payload.side,
        "amount": float(payload.amount),
        "slippage_bps": payload.slippageBps or 0
    })

    if not data or "price" not in data or "expiresAt" not in data:
        raise HTTPException(status_code=500, detail="Pricing engine failed")

    with session_scope() as s:
        q = Quote(
            base=payload.base,
            quote=payload.quote,
            side=payload.side,
            amount=float(payload.amount),
            price=float(data["price"]),
            fee_bps=int(data.get("fee_bps", 25)),
            impact_bps=int(data.get("impact_bps", 0)),
            expires_at=int(data["expiresAt"]),
        )
        s.add(q)
        s.flush()
        return {
            "id": q.id,
            "price": q.price,
            "fee_bps": q.fee_bps,
            "impact_bps": q.impact_bps,
            "expiresAt": q.expires_at,
        }
