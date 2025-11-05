from __future__ import annotations

from dataclasses import dataclass

from .price_utils import bps_deviation, modeled_bps_impact_for_size, route_mid_price_copx_per_col
from .router import quote_col_to_copx
from .twap import TWAPOracle


@dataclass
class GuardedQuote:
    col_in: float
    copx_out_quote: float
    min_out: float
    slip_bps: float


def quote_with_slippage(
    pool_col_x, pool_x_copx, col_in: float, slip_bps: float | None = None, **kwargs
) -> GuardedQuote:
    """
    Build a min-out guard using a slippage tolerance in bps.
    Accepts slip_bps (preferred) or slippage_bps (legacy kw).
    """
    if slip_bps is None:
        slip_bps = kwargs.get("slippage_bps", 0.0)

    q = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
    min_out = q.amount_out * (1.0 - float(slip_bps) / 1e4)
    return GuardedQuote(
        col_in=col_in, copx_out_quote=q.amount_out, min_out=min_out, slip_bps=float(slip_bps)
    )


def size_aware_twap_guard(
    pool_col_x,
    pool_x_copx,
    twap: TWAPOracle,
    col_in: float,
    *,
    base_guard_bps: float = 100.0,
    cushion_bps: float = 150.0,
    cap_bps: float = 2000.0,
) -> tuple[bool, float, float]:
    """
    Compare routed quote vs **TWAP** mid with a size-aware budget:
      budget = min(cap_bps, base_guard_bps + mode led_impact(col_in) + cushion_bps)
    Returns (approved, deviation_bps, budget_bps).
    """
    # Use TWAP baseline (not instantaneous mid) to detect jumps
    twap_mid = float(twap.value())
    if twap_mid <= 0:
        # If TWAP not warmed, fall back to instantaneous mid as a safe default
        twap_mid = route_mid_price_copx_per_col(pool_col_x, pool_x_copx)

    # Quote on current pools
    q = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
    dev_bps = bps_deviation(q.effective_price, twap_mid)

    # Size-aware budget with hard cap
    modeled = modeled_bps_impact_for_size(pool_col_x, pool_x_copx, col_in)
    budget_bps = min(cap_bps, base_guard_bps + modeled + cushion_bps)
    return (dev_bps <= budget_bps, dev_bps, budget_bps)
