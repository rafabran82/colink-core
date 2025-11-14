from fastapi import APIRouter
from colink_core.api.routes.trade import (
    PAPER_BOOK,
    _price_from_ask,
    _price_from_bid,
)

router = APIRouter()

@router.get("/paper/book")
def get_paper_book():
    """
    Return the in-memory PAPER_BOOK state for debugging/admin.
    """
    try:
        return {
            "status": "ok",
            "positions": list(PAPER_BOOK.values()),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
