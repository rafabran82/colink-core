#!/usr/bin/env python3
import argparse
import os
import json
import datetime
import sys
import random
from decimal import Decimal, getcontext

getcontext().prec = 28

CONFIG_PATH = "simulation.config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        config = json.load(f)
    config["meta"]["timestamp"] = datetime.datetime.utcnow().isoformat()
    return config

def init_pools(cfg):
    pools = {}
    for name, p in cfg.get("pools", {}).items():
        pools[name] = {
            "base": p["base"],
            "quote": p["quote"],
            "base_liq": Decimal(str(p["initial_base_liquidity"])),
            "quote_liq": Decimal(str(p["initial_quote_liquidity"])),
            "fee_bps": Decimal(str(p["fee_bps"]))
        }
    return pools

def apply_vol(config, mid):
    sigma = Decimal(str(config["volatility"]["sigma"]))
    drift = Decimal(str(config["volatility"]["drift"]))
    noise = Decimal(str(random.gauss(0, float(sigma))))
    return mid * (Decimal(1) + drift + noise), noise

def compute_spread(mid, base_spread=Decimal("0.0025"), vol_impulse=Decimal("0.5"), noise=Decimal("0")):
    dynamic = base_spread + abs(noise) * vol_impulse
    bid = mid * (Decimal(1) - dynamic)
    ask = mid * (Decimal(1) + dynamic)
    return dynamic, bid, ask

def perform_swap(pool, config):
    if random.random() > 0.05:
        return None

    direction = "COL->XRP" if random.random() < 0.5 else "XRP->COL"
    amount = Decimal(str(random.uniform(100, 3000)))

    base = pool["base_liq"]
    quote = pool["quote_liq"]
    k = base * quote

    if direction == "COL->XRP":
        dx = amount
        new_base = base + dx
        new_quote = k / new_base
        dy = quote - new_quote
        gross = dy
    else:
        dy = amount
        new_quote = quote + dy
        new_base = k / new_quote
        dx = base - new_base
        gross = dx

    amm_fee_bps = pool["fee_bps"]
    xrpay_fee_bps = Decimal(str(config["fees"]["xrpay_fee_bps"]))

    amm_fee = gross * (amm_fee_bps / Decimal(10000))
    xrpay_fee = gross * (xrpay_fee_bps / Decimal(10000))
    net_out = gross - amm_fee - xrpay_fee

    if direction == "COL->XRP":
        pool["base_liq"] = base + dx
        pool["quote_liq"] = quote - net_out
    else:
        pool["quote_liq"] = quote + dy
        pool["base_liq"] = base - net_out

    mid_before = quote / base
    mid_after = pool["quote_liq"] / pool["base_liq"]
    slippage = abs((mid_after - mid_before) / mid_before)

    return {
        "direction": direction,
        "amount": float(amount),
        "amount_out": float(net_out),
        "lp_fee": float(amm_fee),
        "xrpay_fee": float(xrpay_fee),
        "slippage": float(slippage),
        "pool_base_after": float(pool["base_liq"]),
        "pool_quote_after": float(pool["quote_liq"])
    }

def main():
    parser = argparse.ArgumentParser(description="COLINK Simulation (Phase 3)")
    parser.add_argument("--out", default=".artifacts/data")
    parser.add_argument("--replay", default=None)
    parser.add_argument("--step", type=int, default=None)
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)
    random.seed(config["simulation"]["random_seed"])

    # === LP SHARE MODEL ===
    lp_shares_total = Decimal("1000000")
    lp_shares_user = Decimal("1000000")

    # Initial pool value
    pool0 = list(pools.values())[0]
    init_base = pool0["base_liq"]
    init_quote = pool0["quote_liq"]
    init_mid = init_quote / init_base
    initial_pool_value = float(init_base) * float(init_mid) + float(init_quote)

    # === A22: LP Drawdown Tracking ===
    lp_value_peak = initial_pool_value
    lp_value_trough = initial_pool_value
    lp_value_prev = initial_pool_value
    lp_vol_sum = 0.0
    lp_vol_count = 0

    # === A23: Shock Detection ===
    shock_events = []
    shock_count_price = 0
    shock_count_slip = 0
    shock_count_vol = 0
    shock_count_lp = 0

    last_mid = float(init_mid)
    last_lp_value = initial_pool_value

    # --- REPLAY LOADING ---
    replay_data = []
    if args.replay:
        with open(args.replay, "r", encoding="utf-8") as f:
            replay_data = json.load(f)

    # --- rest of main() continues exactly as before, normalized ---if __name__ == "__main__":
    main()




















