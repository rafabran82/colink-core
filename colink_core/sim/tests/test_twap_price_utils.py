from colink_core.sim.amm import PoolState
from colink_core.sim.twap import TWAPOracle
from colink_core.sim.price_utils import route_mid_price_copx_per_col, bps_deviation

def seed():
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    pool_col_x  = PoolState(x_reserve=10_000.0, y_reserve=200_000.0,   fee_bps=30)
    return pool_col_x, pool_x_copx

def test_twap_warm_and_value_stable():
    a, b = seed()
    tw = TWAPOracle(window=5)
    mid = route_mid_price_copx_per_col(a, b)
    tw.warm([mid]*5)
    assert abs(tw.value() - mid) < 1e-12

def test_bps_deviation_zero_when_equal():
    assert bps_deviation(100.0, 100.0) == 0.0

def test_bps_deviation_positive_when_below_twap():
    dev = bps_deviation(95.0, 100.0)
    assert 499.0 < dev < 501.0  # ~500 bps

