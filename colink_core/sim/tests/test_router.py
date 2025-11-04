from colink_core.sim.amm import PoolState
from colink_core.sim.router import exec_col_to_copx, quote_col_to_copx


def seed():
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    pool_col_x  = PoolState(x_reserve=10_000.0, y_reserve=200_000.0,   fee_bps=30)  # ~20 COL per XRP
    return pool_col_x, pool_x_copx

def test_quote_and_exec_are_positive_and_reasonable():
    a, b = seed()
    q = quote_col_to_copx(a, b, 5_000.0)
    assert q.amount_out > 0
    # execution on fresh copies should be close to quoted (identical math path)
    a2, b2 = seed()
    r = exec_col_to_copx(a2, b2, 5_000.0)
    assert abs(r.amount_out - q.amount_out) / q.amount_out < 1e-9

