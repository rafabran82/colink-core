from colink_core.sim.limits import TradeLimiter, LimitConfig

def test_limiter_size_and_dev_caps_and_breaker():
    cfg = LimitConfig(max_col_in=25_000.0, max_dev_bps=2_000.0, strikes_window=2, cooldown_trades=3)
    lim = TradeLimiter(cfg)

    # ok trade
    ok, reason = lim.check_and_record(10_000.0, 900.0)
    assert ok

    # two violations trip breaker
    ok, reason = lim.check_and_record(30_000.0, 100.0)  # size breach
    assert not ok and "size_exceeds_cap" in reason
    ok, reason = lim.check_and_record(5_000.0, 3_000.0) # dev breach
    assert not ok and lim.tripped

    # while tripped, can_trade blocks and ticks cooldown
    ok, reason = lim.can_trade()
    assert not ok and "circuit_breaker_tripped" in reason

    # simulate cooldown ticks
    for _ in range(cfg.cooldown_trades):
        lim.can_trade()

    # first request after auto-reset tells caller to re-quote
    ok, reason = lim.check_and_record(10_000.0, 100.0)
    assert not ok and "auto_reset" in reason


