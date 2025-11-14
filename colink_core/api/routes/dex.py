from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import settings
from xrpl_utils import cancel_offer, client_from, create_offer, list_offers, orderbook_snapshot

router = APIRouter()


class OfferBody(BaseModel):
    side: str  # "SELL_COL" or "BUY_COL"
    iou: str
    xrp: str


@router.post("/offer")
def post_offer(body: OfferBody):
    try:
        if not settings.TRADER_SEED or not settings.ISSUER_ADDRESS:
            raise ValueError("Missing TRADER_SEED or ISSUER_ADDRESS in settings.")
        c = client_from(settings.XRPL_RPC_URL)
        res = create_offer(
            c,
            body.side,
            settings.TRADER_SEED,
            settings.ISSUER_ADDRESS,
            settings.COL_CODE,
            body.iou,
            body.xrp,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/offers")
def get_offers():
    try:
        if not settings.TRADER_SEED:
            raise ValueError("Missing TRADER_SEED in settings.")
        c = client_from(settings.XRPL_RPC_URL)
        return list_offers(c, settings.TRADER_SEED)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/offers/{seq}")
def delete_offer(seq: int):
    try:
        if not settings.TRADER_SEED:
            raise ValueError("Missing TRADER_SEED in settings.")
        c = client_from(settings.XRPL_RPC_URL)
        return cancel_offer(c, settings.TRADER_SEED, seq)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/orderbook")
def get_orderbook(limit: int = Query(default=20, ge=1, le=400)):
    try:
        if not settings.ISSUER_ADDRESS:
            raise ValueError("Missing ISSUER_ADDRESS (env COL_ISSUER).")
        c = client_from(settings.XRPL_RPC_URL)
        return orderbook_snapshot(c, settings.ISSUER_ADDRESS, settings.COL_CODE, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
