from fastapi import APIRouter, HTTPException

from config import settings
from xrpl_utils import client_from, fetch_col_state

router = APIRouter()


@router.get("/status")
def status():
    try:
        if not settings.ISSUER_ADDRESS:
            raise ValueError("Missing ISSUER_ADDRESS (env COL_ISSUER).")
        if not settings.TRADER_SEED:
            raise ValueError("Missing TRADER_SEED (env COL_TRADER_SEED).")

        c = client_from(settings.XRPL_RPC_URL)
        state = fetch_col_state(c, settings.TRADER_SEED, settings.ISSUER_ADDRESS, settings.COL_CODE)
        return {
            "rpc_url": settings.XRPL_RPC_URL,
            "col_code": settings.COL_CODE,
            "col_decimals": settings.COL_DECIMALS,
            **state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
