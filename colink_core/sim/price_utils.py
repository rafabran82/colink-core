from __future__ import annotations

from .amm import PoolState


# ----- Mid-price helpers -----
def mid_route_price_col_to_copx(pool_col_x: PoolState, pool_x_copx: PoolState) -> float:
    """
    Mid (no-impact) price for COLâ†’XRPâ†’COPX.
    pool_col_x: X=XRP, Y=COL  â‡’  XRP per COL = X/Y
    pool_x_copx: X=XRP, Y=COPX â‡’ COPX per XRP = Y/X
    mid (COPX per COL) = (XRP/COL) * (COPX/XRP)
    """
    xrp_per_col = pool_col_x.x_reserve / pool_col_x.y_reserve
    copx_per_xrp = pool_x_copx.y_reserve / pool_x_copx.x_reserve
    return xrp_per_col * copx_per_xrp


# Backward-compatible alias expected by risk_guard.py
def route_mid_price_copx_per_col(pool_col_x: PoolState, pool_x_copx: PoolState) -> float:
    return mid_route_price_col_to_copx(pool_col_x, pool_x_copx)


# ----- Deviation / impact helpers -----
def bps_deviation(effective: float, reference: float) -> float:
    """
    Return absolute deviation in basis points between effective and reference prices:
    dev_bps = |effective - reference| / reference * 1e4
    """
    if reference <= 0:
        return 0.0
    return abs(effective - reference) / reference * 1e4


def modeled_bps_impact_for_size(
    pool_col_x: PoolState, pool_x_copx: PoolState, col_in: float
) -> float:
    """
    Estimate price impact (in bps) for a COLâ†’COPX trade of size `col_in`,
    comparing the routed effective price vs the mid price.
    """
    if col_in <= 0:
        return 0.0

    mid = mid_route_price_col_to_copx(pool_col_x, pool_x_copx)
    if mid <= 0:
        return 0.0

    # Use the router's non-mutating quote
    from .router import quote_col_to_copx

    q = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
    eff = q.effective_price  # COPX per COL

    # Impact as bps below mid (never negative)
    impact_frac = max(0.0, (mid - eff) / mid)
    return impact_frac * 1e4  # â†’ bps

