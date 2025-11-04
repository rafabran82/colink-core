from fastapi import APIRouter

from config import settings

router = APIRouter(prefix="/_debug", tags=["debug"])

def _mask(s: str, keep: int = 4) -> str:
    if not s:
        return ""
    if len(s) <= keep:
        return "*" * len(s)
    return s[:keep] + "*" * (len(s) - keep)

@router.get("/settings")
def debug_settings():
    return {
        "rpc_url": settings.rpc_url,
        "col_code": settings.col_code,
        "col_decimals": settings.col_decimals,
        "issuer_addr": settings.issuer_addr,
        "trader_addr": settings.trader_addr,
        "issuer_seed_masked": _mask(settings.issuer_seed),
        "trader_seed_masked": _mask(settings.trader_seed),
        "issuer_seed_error": settings.issuer_seed_error,
        "trader_seed_error": settings.trader_seed_error,
        "paper_mode": settings.paper_mode,
    }
