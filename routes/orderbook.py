from typing import Any

from fastapi import APIRouter, HTTPException

from config import settings
from xrpl_utils import client_from, orderbook_snapshot

router = APIRouter(prefix="", tags=["orderbook"])

@router.get("/orderbook")
def get_orderbook(limit: int = 20) -> Any:
    try:
        client = client_from(settings.rpc_url)
        ob = orderbook_snapshot(client, settings.issuer_addr, settings.col_code, limit=limit)
        # Basic shape sanity to avoid serialization surprises
        if not isinstance(ob, dict) or "bids" not in ob or "asks" not in ob:
            raise ValueError("Malformed orderbook payload")
        return ob
    except Exception as e:
        # Return a 400 with useful detail (instead of a 500)
        raise HTTPException(status_code=400, detail={"error": str(e) from e, "type": e.__class__.__name__}) from e





