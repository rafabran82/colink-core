from fastapi import APIRouter

from config import settings
from models import TrustlineReq
from xrpl_utils import client_from, ensure_trustline

router = APIRouter()


@router.post("/trustline")
def trustline(body: TrustlineReq):
    c = client_from(settings.XRPL_RPC_URL)
    res = ensure_trustline(
        c, settings.TRADER_SEED, settings.COL_ISSUER, settings.COL_CODE, body.limit
    )
    return res
