from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

# Temporary in-memory responses until sim/bridge wiring is complete

@router.get("/sim/meta")
async def get_sim_meta():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": "local-dev",
        "params": {
            "note": "placeholder response from backend"
        }
    }


@router.get("/pools/state")
async def get_pools_state():
    return [
        {
            "name": "COL/XRP",
            "volume": 0,
            "liquidity": 0
        },
        {
            "name": "COPX/COL",
            "volume": 0,
            "liquidity": 0
        }
    ]


@router.get("/swaps/recent")
async def get_swaps_recent():
    return [
        {
            "pair": "COL/XRP",
            "amount": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
