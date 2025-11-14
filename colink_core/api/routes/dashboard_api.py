from fastapi import APIRouter

router = APIRouter()

@router.get("/sim/meta")
def get_sim_meta():
    return {
        "timestamp": "2025-01-01T00:00:00Z",
        "engine": "demo",
        "status": "ok"
    }

@router.get("/pools/state")
def get_pools_state():
    return [
        {"pair": "COPX/COL", "reserve1": 1000, "reserve2": 7800},
        {"pair": "COL/XRP", "reserve1": 15000, "reserve2": 270}
    ]

@router.get("/swaps/recent")
def get_swap_logs():
    return [
        {"pair": "COPX/COL", "amount_in": 1000, "amount_out": 7800, "timestamp": "2025-01-01T00:00:00Z"},
        {"pair": "COL/XRP", "amount_in": 15000, "amount_out": 270, "timestamp": "2025-01-01T00:05:00Z"}
    ]
