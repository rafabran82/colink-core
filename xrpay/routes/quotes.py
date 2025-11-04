from fastapi import APIRouter, Body, HTTPException
from ..services.pricing import PricingEngine
from ..liquidity.sim_provider import SimProvider
from ..db import session_scope
from ..models import Quote
from decimal import Decimal, InvalidOperation

router = APIRouter(prefix="/quotes", tags=["quotes"])

_provider = SimProvider()
_engine = PricingEngine(_provider)

@router.post("")
def create_quote(payload: dict = Body(...)):
    base  = payload.get("base")
    quote = payload.get("quote")
    side  = payload.get("side")
    amount_raw = payload.get("amount")
    slippage = payload.get("slippageBps") or payload.get("slippage_bps")
    if slippage is None:
        slippage = 50

    try:
        amount = Decimal(str(amount_raw))
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=400, detail="invalid amount")

    # Normalize to provider’s expected naming (camelCase)
    q = _engine.quote({
        "base": base,
        "quote": quote,
        "side": side,
        "amount": str(amount),
        "slippageBps": int(slippage),
    })

    # Persist
    with session_scope() as s:
        row = Quote(
            base=base, quote=quote, side=side,
            amount=str(amount),
            price=str(q["price"]),
            fee_bps=q.get("fee_bps", 0),
            impact_bps=q.get("impact_bps", 0),
            expires_at=q.get("expiresAt"),
        )
        s.add(row)
        s.flush()
        return {
            "id": row.id,
            "price": float(row.price),
            "fee_bps": row.fee_bps,
            "impact_bps": row.impact_bps,
            "expiresAt": row.expires_at,
        }
