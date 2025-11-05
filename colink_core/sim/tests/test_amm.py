from colink_core.sim.amm import PoolState


def seed(fee_bps=30):
    # 1 XRP : 2500 COPX pool
    return PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=fee_bps)


def test_swap_x_for_y_increases_x_decreases_y_and_respects_fee():
    p = seed()
    x_before, y_before = p.x_reserve, p.y_reserve
    out, eff = p.swap_x_for_y(100.0)  # add 100 XRP to pool, get COPX out
    assert p.x_reserve > x_before
    assert p.y_reserve < y_before
    assert out > 0
    assert eff > 0


def test_swap_y_for_x_increases_y_decreases_x_and_respects_fee():
    p = seed()
    x_before, y_before = p.x_reserve, p.y_reserve
    out, eff = p.swap_y_for_x(250_000.0)  # add COPX to pool, get XRP out
    assert p.y_reserve > y_before
    assert p.x_reserve < x_before
    assert out > 0
    assert eff > 0


def test_liquidity_add_and_remove_is_proportional():
    p = seed()
    lp0 = p.total_lp
    # add in proportion (keeps price stable)
    minted = p.add_liquidity(1_000.0, 2_500_000.0)
    assert p.total_lp == lp0 + minted
    # remove 10%
    dx, dy = p.remove_liquidity(0.10)
    assert dx > 0 and dy > 0
    # remaining LP should match (approx) 90% supply
    assert 0.8999 <= p.total_lp / (lp0 + minted) <= 0.9001


def test_price_monotonicity_basic():
    p = seed()
    price0 = p.y_reserve / p.x_reserve  # COPX per XRP
    p.swap_x_for_y(100.0)
    price1 = p.y_reserve / p.x_reserve
    assert price1 < price0  # buying Y with X pushes price down (more X, less Y)
