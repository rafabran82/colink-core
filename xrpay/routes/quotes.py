from xrpay.deps import require_idempotency_key, require_fresh_timestamp
from datetime import datetime, timedelta
from fastapi import \1, Depends
from pydantic import BaseModel, Field
from typing import Literal, List

from ..db import session_scope
from ..models import Quote

router = APIRouter(prefix="/quotes", tags=["quotes"])

# ----- Request/Response models -----
class QuoteRequest(BaseModel):
    base:  str
    quote: str
    side:  Literal["BUY", "SELL"]
    amount: float = Field(gt=0)
    slippageBps: int = Field(ge=0, le=10_000)

class QuoteResponse(BaseModel):
    id: int
    price: float
    fee_bps: int
    impact_bps: int
    expiresAt: int

# ----- Helpers (stub pricing logic) -----
def _price_for_pair(base: str, quote: str) -> float:
    # placeholder — deterministic for test flows
    if (base, quote) == ("XRP", "USD"):
        return 0.6015
    return 1.0

# ----- POST /quotes  (persist + return id) -----
@router.post("", response_model=QuoteResponse)
def make_quote(req: QuoteRequest):
    price = _price_for_pair(req.base, req.quote)

    # Simple “impact” model using requested slippage
    impact_bps = int(req.slippageBps)
    fee_bps    = 25  # flat fee for demo
    # 60s TTL is fine for tests
    expires_at = int((datetime.utcnow() + timedelta(seconds=60)).timestamp())

    with session_scope() as s:
        q = Quote(
            base=req.base,
            quote=req.quote,
            side=req.side,
            amount=req.amount,
            price=price,
            fee_bps=fee_bps,
            impact_bps=impact_bps,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
        s.add(q)
        s.flush()  # assigns q.id
        return QuoteResponse(
            id=q.id,
            price=q.price,
            fee_bps=q.fee_bps,
            impact_bps=q.impact_bps,
            expiresAt=q.expires_at,
        )

# ----- GET /quotes/_debug/quotes  (safe lister) -----
@router.get("/_debug/quotes")
def list_quotes() -> List[dict]:
    with session_scope() as s:
        rows = s.query(Quote).order_by(Quote.id.desc()).limit(25).all()
        return [
            {
                "id": r.id,
                "base": r.base,
                "quote": r.quote,
                "side": r.side,
                "amount": r.amount,
                "price": r.price,
                "fee_bps": r.fee_bps,
                "impact_bps": r.impact_bps,
                "expires_at": r.expires_at,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]



