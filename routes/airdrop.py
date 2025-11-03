from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
from xrpl_utils import client_from, iou_payment

router = APIRouter()

class AirdropBody(BaseModel):
    to: str
    amount: str

@router.post("/airdrop")
def airdrop(body: AirdropBody):
    try:
        if not settings.ISSUER_SEED:
            raise ValueError("Missing ISSUER_SEED (env COL_ISSUER_SEED).")
        c = client_from(settings.XRPL_RPC_URL)
        res = iou_payment(c, settings.ISSUER_SEED, body.to, settings.COL_CODE, body.amount)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
