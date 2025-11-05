from __future__ import annotations

from amm import PoolState
from price_utils import bps_deviation, route_mid_price_copx_per_col
from risk_guard import size_aware_twap_guard
from router import quote_col_to_copx
from twap import TWAPOracle

from limits import LimitConfig, TradeLimiter


def fmt(n: float) -> str:
    return f"{n:,.6f}"


def seed():
    # Same pools used across the project
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    pool_col_x = PoolState(x_reserve=10_000.0, y_reserve=200_000.0, fee_bps=30)
    return pool_col_x, pool_x_copx


def main():
    poolA, poolB = seed()

    # Warm TWAP with route mid
    twap = TWAPOracle(window=8)
    mid0 = route_mid_price_copx_per_col(poolA, poolB)
    twap.warm([mid0] * 8)
    print("TWAP warmed. Initial TWAP =", fmt(twap.value()), " COPX/COL\n")

    # Limiter with reasonable defaults (tweak as desired)
    limiter = TradeLimiter(
        LimitConfig(
            max_col_in=25_000.0,
            max_dev_bps=2_000.0,
            strikes_window=3,
            cooldown_trades=5,
        )
    )

    # Try a sequence of sizes; last two should breach (size & dev), stacking strikes
    sizes = [500, 5_000, 10_000, 25_000, 50_000]

    for i, col_in in enumerate(sizes, 1):
        q = quote_col_to_copx(poolA, poolB, col_in)
        eff = q.effective_price
        tw = twap.value()
        dev = bps_deviation(eff, tw)

        # TWAP size-aware guard first (quotes vs modeled budget)
        ok_guard, dev_bps, budget_bps = size_aware_twap_guard(
            poolA, poolB, twap, col_in, base_guard_bps=100.0, cushion_bps=150.0, cap_bps=2_000.0
        )

        # Then hard limits / circuit breaker
        ok_limiter, reason = limiter.check_and_record(col_in, dev)

        print(
            f"[{i}] size={fmt(col_in)} COL | eff={fmt(eff)} TWAP={fmt(tw)} dev={dev:.1f}bps "
            f"| guard={'OK' if ok_guard else f'BLOCK ({dev_bps:.1f}>{budget_bps:.1f}bps)'} "
            f"| limit={'OK' if ok_limiter else 'BLOCK'} ({reason}) "
            f"| strikes={limiter.strikes} tripped={limiter.tripped}"
        )

    # Demonstrate breaker cooldown ticking
    if limiter.tripped:
        print("\nCircuit breaker is TRIPPED. Simulating cooldown...")
        for j in range(1, 7):
            ok, reason = limiter.can_trade()
            print(f" cooldown tick {j}: {('OK' if ok else 'BLOCK')} ({reason})")


if __name__ == "__main__":
    main()
