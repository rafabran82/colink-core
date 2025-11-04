from fastapi import APIRouter, Body
from ..services.pricing import PricingEngine
from ..liquidity.sim_provider import SimProvider
from ..repos import create_quote

router = APIRouter(prefix="/quotes", tags=["quotes"])

_provider = SimProvider()
_engine = PricingEngine(_provider)

@router.post("")
async def make_quote(payload: dict = Body(...)):
    # Ask engine, then persist a Quote with 30s TTL
    data = await _engine.quote(payload)
    q = create_quote(
        base=payload["base"],
        quote=payload["quote"],
        side=payload.get("side","BUY"),
        amount=str(payload["amount"]),
        price=str(data["price"]),
        fee_bps=int(data["fee_bps"]),
        impact_bps=int(data["impact_bps"]),
        ttl_sec=30
    )
    return {
        "id": q.id,
        "price": q.price,
        "fee_bps": q.fee_bps,
        "impact_bps": q.impact_bps,
        "expiresAt": q.expires_at,
        "status": q.status
    }
