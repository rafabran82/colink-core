from fastapi import APIRouter

from routes.trade import PAPER_BOOK, _price_from_ask, _price_from_bid

router = APIRouter(prefix="/_paper", tags=["paper"])


@router.get("/book")
def get_paper_book():
    # Return a sorted snapshot for easier reading
    asks = sorted(PAPER_BOOK["asks"], key=_price_from_ask)
    bids = sorted(PAPER_BOOK["bids"], key=_price_from_bid, reverse=True)
    return {"bids": bids, "asks": asks}


@router.post("/clear")
def clear_paper_book():
    PAPER_BOOK["bids"].clear()
    PAPER_BOOK["asks"].clear()
    return {"ok": True, "message": "paper book cleared"}

