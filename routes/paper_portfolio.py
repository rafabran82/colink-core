from fastapi import APIRouter
from decimal import Decimal
from typing import Any, Dict

from routes.trade import PAPER_POSITION

router = APIRouter(prefix="/_paper", tags=["paper-portfolio"])

def _s(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, Decimal):
        return str(x)
    return str(x)

@router.get("/position")
def get_position():
    return {
        "col": _s(PAPER_POSITION["col"]),
        "xrp": _s(PAPER_POSITION["xrp"]),
        "avg_price_xrp_per_col": _s(PAPER_POSITION["avg_price"]),
        "realized_pnl_xrp": _s(PAPER_POSITION["realized_pnl_xrp"]),
    }

@router.post("/position/reset")
def reset_position():
    PAPER_POSITION["col"] = Decimal("0")
    PAPER_POSITION["xrp"] = Decimal("0")
    PAPER_POSITION["avg_price"] = None
    PAPER_POSITION["realized_pnl_xrp"] = Decimal("0")
    return {"ok": True, "message": "paper position reset"}

