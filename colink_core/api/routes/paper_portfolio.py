from fastapi import APIRouter
from colink_core.api.routes.trade import PAPER_POSITION

router = APIRouter()

@router.get("/paper/portfolio")
def get_paper_portfolio():
    """
    Return the in-memory PAPER_POSITION map.
    """
    try:
        return {
            "status": "ok",
            "positions": list(PAPER_POSITION.values()),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
