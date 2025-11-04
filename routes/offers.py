from fastapi import APIRouter, HTTPException
from config import settings
from models import OfferReq
from xrpl_utils import client_from, create_offer, list_offers, cancel_offer

router = APIRouter()

@router.post("/offer")
def place_offer(body: OfferReq):
    if body.side not in ("SELL_COL", "BUY_COL"):
        raise HTTPException(400, "side must be SELL_COL or BUY_COL")
    c = client_from(settings.XRPL_RPC_URL)
    res = create_offer(c, body.side, settings.TRADER_SEED, settings.COL_ISSUER, settings.COL_CODE, body.iou, body.xrp)
    return res

@router.get("/offers")
def my_offers():
    c = client_from(settings.XRPL_RPC_URL)
    return list_offers(c, settings.TRADER_SEED)

@router.delete("/offers/{seq}")
def cancel(seq: int):
    c = client_from(settings.XRPL_RPC_URL)
    return cancel_offer(c, settings.TRADER_SEED, seq)

