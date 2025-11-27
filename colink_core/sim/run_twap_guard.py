from __future__ import annotations

import time
from copy import deepcopy

from amm import PoolState
from price_utils import bps_deviation, route_mid_price_copx_per_col
from risk_guard import allowed_deviation_bps
from router import exec_col_to_copx, quote_col_to_copx
from twap import TWAP


def fmt(n):
    return f"{n:,.6f}"


def seed():
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    pool_col_x = PoolState(x_reserve=10_000.0, y_reserve=200_000.0, fee_bps=30)
    return pool_col_x, pool_x_copx


def warm_twap(twap, poolA, poolB, steps=12, dt=2.0):
    now = time.time()
    for i in range(steps):
        px = route_mid_price_copx_per_col(poolA, poolB)
        twap.add(px, now + i * dt)


def try_fill_with_twap_guard(
    poolA,
    poolB,
    col_in: float,
    twap: TWAP,
    base_band_bps: float = 100.0,
    cushion_bps: float = 150.0,
):
    # Non-mutating quote
    q = quote_col_to_copx(poolA, poolB, col_in)
    quote_px = q.effective_price
    ref_px = twap.value()
    dev = bps_deviation(quote_px, ref_px)

    # Size-aware budget (fees+slippage for this size) + bands
    allowed = allowed_deviation_bps(col_in, poolA, poolB, base_band_bps, cushion_bps)
    print(
        f"Quote: {fmt(col_in)} COL -> {fmt(q.amount_out)} COPX | px={fmt(quote_px)}  TWAP={fmt(ref_px)}  dev={dev:.1f} bps"
    )
    print(
        f"Guard budget: â‰¤ {allowed:.1f} bps (base {base_band_bps:.0f} + modeled-impact + cushion {cushion_bps:.0f})"
    )

    if dev > allowed:
        print(f"â€¼ï¸  Refused by TWAP guard: deviation {dev:.1f} bps > {allowed:.1f} bps\n")
        return False

    # Mutating execution against fresh copies to simulate immediate fill
    A2, B2 = deepcopy(poolA), deepcopy(poolB)
    r_exec = exec_col_to_copx(A2, B2, col_in)
    print(
        f"Exec:  {fmt(col_in)} COL -> {fmt(r_exec.amount_out)} COPX | eff={fmt(r_exec.effective_price)}\n"
    )
    return True


def main():
    poolA, poolB = seed()
    tw = TWAP(window_sec=60)

    warm_twap(tw, poolA, poolB)
    print("TWAP warmed. Initial TWAP =", fmt(tw.value()), " COPX/COL\n")

    # Case 1: Normal market (should PASS now)
    try_fill_with_twap_guard(poolA, poolB, col_in=5_000.0, twap=tw)

    # Small drift (should still PASS)
    poolB.swap_x_for_y(150.0)  # nudge COPX/XRP
    warm_twap(tw, poolA, poolB, steps=3, dt=2.0)
    try_fill_with_twap_guard(poolA, poolB, col_in=5_000.0, twap=tw)

    # Case 2: Adverse move â€” should FAIL
    poolB.swap_y_for_x(5_000_000.0)  # big COPX->XRP (drops COPX/XRP)
    poolA.swap_y_for_x(50_000.0)  # big COL->XRP (drains X on COL/X)
    print(
        "Applied adverse moves to pools (pre-quote). Mid route price now:",
        fmt(route_mid_price_copx_per_col(poolA, poolB)),
        " COPX/COL",
    )
    try_fill_with_twap_guard(poolA, poolB, col_in=5_000.0, twap=tw)


if __name__ == "__main__":
    main()

