from fastapi import APIRouter
from ..db import session_scope
from ..models import Quote

router = APIRouter(tags=["_debug"])

@router.get("/_debug/quotes")
def debug_quotes(limit: int = 10):
    with session_scope() as s:
        rows = (
            s.query(Quote)
             .order_by(Quote.id.desc())
             .limit(limit)
             .all()
        )
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
