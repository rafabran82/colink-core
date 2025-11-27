from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from .amm import PoolState


@dataclass
class RouteResult:
    amount_in: float
    amount_out: float
    effective_price: float
    hop1_out: float
    hop2_out: float


def _swap_copy(pool: PoolState, side: str, amt: float) -> tuple[float, float, PoolState]:
    """Side = 'x_for_y' or 'y_for_x'. Returns (out, eff_px, new_pool_copy)."""
    p = deepcopy(pool)
    if side == "x_for_y":
        out, eff = p.swap_x_for_y(amt)
    elif side == "y_for_x":
        out, eff = p.swap_y_for_x(amt)
    else:
        raise ValueError("side must be 'x_for_y' or 'y_for_x'")
    return out, eff, p


def quote_col_to_copx(pool_col_x: PoolState, pool_x_copx: PoolState, col_in: float) -> RouteResult:
    """
    Hop1: COL -> XRP on pool_col_x (COL treated as Y, XRP as X: use y_for_x).
    Hop2: XRP -> COPX on pool_x_copx (x_for_y).
    Does NOT mutate original pools.
    """
    xrp_out, _eff1, _tmp = _swap_copy(pool_col_x, "y_for_x", col_in)
    copx_out, _eff2, _tmp2 = _swap_copy(pool_x_copx, "x_for_y", xrp_out)
    eff_price = copx_out / col_in if col_in > 0 else 0.0
    return RouteResult(col_in, copx_out, eff_price, xrp_out, copx_out)


def quote_copx_to_col(pool_col_x: PoolState, pool_x_copx: PoolState, copx_in: float) -> RouteResult:
    """
    Hop1: COPX -> XRP on pool_x_copx (y_for_x).
    Hop2: XRP -> COL on pool_col_x (x_for_y).
    Does NOT mutate original pools.
    """
    xrp_out, _eff1, _tmp = _swap_copy(pool_x_copx, "y_for_x", copx_in)
    col_out, _eff2, _tmp2 = _swap_copy(pool_col_x, "x_for_y", xrp_out)
    eff_price = col_out / copx_in if copx_in > 0 else 0.0
    return RouteResult(copx_in, col_out, eff_price, xrp_out, col_out)


def exec_col_to_copx(pool_col_x: PoolState, pool_x_copx: PoolState, col_in: float) -> RouteResult:
    """Mutating execution of COLâ†’XRPâ†’COPX."""
    xrp_out, _ = pool_col_x.swap_y_for_x(col_in)
    copx_out, _ = pool_x_copx.swap_x_for_y(xrp_out)
    eff_price = copx_out / col_in if col_in > 0 else 0.0
    return RouteResult(col_in, copx_out, eff_price, xrp_out, copx_out)


def exec_copx_to_col(pool_col_x: PoolState, pool_x_copx: PoolState, copx_in: float) -> RouteResult:
    """Mutating execution of COPXâ†’XRPâ†’COL."""
    xrp_out, _ = pool_x_copx.swap_y_for_x(copx_in)
    col_out, _ = pool_col_x.swap_x_for_y(xrp_out)
    eff_price = col_out / copx_in if copx_in > 0 else 0.0
    return RouteResult(copx_in, col_out, eff_price, xrp_out, col_out)

