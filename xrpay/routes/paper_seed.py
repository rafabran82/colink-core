from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["paper-dev"])

class SeedReq(BaseModel):
    base: str = "XRP"
    quote: str = "USD"
    mid: float = Field(0.5, gt=0)
    spreadBps: int = Field(20, ge=0)     # total spread
    levels: int = Field(5, ge=1)
    depthPerLevel: float = Field(1000, gt=0)

@router.post("/_paper/seed")
def seed_book(req: SeedReq):
    try:
        # Minimal synthetic book: levels of bids/asks around mid
        # Replace with your actual paper engine calls if available
        import math
        bps = req.spreadBps / 10000
        half = bps / 2.0
        bids = []
        asks = []
        for i in range(1, req.levels + 1):
            # widen linearly with level
            px_b = req.mid * (1 - half * i / req.levels)
            px_a = req.mid * (1 + half * i / req.levels)
            bids.append({"price": round(px_b, 6), "size": req.depthPerLevel})
            asks.append({"price": round(px_a, 6), "size": req.depthPerLevel})
        # stash to a module-level singleton for demo
        global _BOOK
        _BOOK = {"pair": f"{req.base}/{req.quote}", "mid": req.mid, "bids": bids, "asks": asks}
        return {"status": "ok", "levels": req.levels, "pair": _BOOK["pair"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/_paper/book")
def get_book():
    if "_BOOK" not in globals():
        raise HTTPException(status_code=404, detail="No paper book seeded.")
    return _BOOK

@router.post("/_paper/clear")
def clear_book():
    globals().pop("_BOOK", None)
    return {"status": "cleared"}
