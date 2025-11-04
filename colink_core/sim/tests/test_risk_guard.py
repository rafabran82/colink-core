from colink_core.sim.amm import PoolState
from colink_core.sim.price_utils import route_mid_price_copx_per_col
from colink_core.sim.risk_guard import quote_with_slippage, size_aware_twap_guard
from colink_core.sim.router import quote_col_to_copx
from colink_core.sim.twap import TWAPOracle


def seed():
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    pool_col_x  = PoolState(x_reserve=10_000.0, y_reserve=200_000.0,   fee_bps=30)
    return pool_col_x, pool_x_copx

def test_min_out_guard_allows_small_slippage():
    a, b = seed()
    col_in = 8_000.0
    gq = quote_with_slippage(a, b, col_in, slip_bps=150.0)
    q  = quote_col_to_copx(a, b, col_in)
    assert q.amount_out >= gq.min_out  # identical pools => should pass

def test_size_aware_twap_guard_blocks_large_deviation():
    a, b = seed()
    # warm TWAP with current mid
    tw = TWAPOracle(window=8)
    mid = route_mid_price_copx_per_col(a, b)
    tw.warm([mid]*8)
    # artificially skew the pool to create large deviation (push price down)
    b.swap_x_for_y(2_000.0)  # buy lots of COPX with XRP
    ok, dev_bps, budget_bps = size_aware_twap_guard(a, b, tw, 25_000.0, base_guard_bps=100.0, cushion_bps=150.0, cap_bps=2_000.0)
    assert not ok
    assert dev_bps > budget_bps

