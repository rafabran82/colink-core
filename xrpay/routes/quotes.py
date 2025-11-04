from __future__ import annotations

from decimal import Decimal
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..db import session_scope
from ..models import Quote
from ..services.pricing import provider

router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuoteRequest(BaseModel):
    base: str = Field(..., description="Base asset symbol, e.g. XRP")
    quote: str = Field(..., description="Quote asset symbol, e.g. USD")
    side: Literal["BUY", "SELL"]
    amount: Decimal
    # Support both notations from clients
    slippageBps: Optional[int] = Field(None, ge=0, le=10_000)
    slippage_bps: Optional[int] = Field(None, ge=0, le=10_000)

    def normalized_slippage(self) -> int:
        if self.slippage_bps is not None:
            return self.slippage_bps
        if self.slippageBps is not None:
            return self.slippageBps
        return 25


@router.post("")
def create_quote(req: QuoteRequest):
    try:
        q = provider.get_quote(
            base=req.base,
            quote=req.quote,
            side=req.side,
            amount=req.amount,
            slippage_bps=req.normalized_slippage(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"quote_error: {e}")

    with session_scope() as s:
        quote = Quote(
            base=req.base.upper(),
            quote=req.quote.upper(),
            side=req.side.upper(),
            amount=str(req.amount),
            price=str(Decimal(str(q["price"]))),
            fee_bps=int(q["fee_bps"]),
            impact_bps=int(q["impact_bps"]),
            expires_at=int(q["expires_at"]),
        )
        s.add(quote)
        s.flush()
        quote_id = quote.id

    return {
        "id": quote_id,
        "price": float(Decimal(str(q["price"]))),
        "fee_bps": int(q["fee_bps"]),
        "impact_bps": int(q["impact_bps"]),
        "expiresAt": int(q["expires_at"]),
    }
