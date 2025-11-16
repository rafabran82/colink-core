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
    """Attempt a swap with probability ~5%."""
    if random.random() > 0.05:
        return None  # no trade

    # Trade direction
    direction = "COL->XRP" if random.random() < 0.5 else "XRP->COL"

    # Trade amount (COL or XRP side)
    amount = Decimal(str(random.uniform(100, 3000)))

    base = pool["base_liq"]
    quote = pool["quote_liq"]

    if direction == "COL->XRP":
        dx = amount
        x = base
        y = quote
        k = x * y
        new_x = x + dx
        new_y = k / new_x
        dy = y - new_y
    else:
        dy = amount
        x = base
        y = quote
        k = x * y
        new_y = y + dy
        new_x = k / new_y
        dx = x - new_x

    # fees ------------------------------------
    amm_fee_bps = pool["fee_bps"]
    xrpay_fee_bps = Decimal(str(config["fees"]["xrpay_fee_bps"]))

    gross_out = dy if direction == "COL->XRP" else dx

    amm_fee = gross_out * (amm_fee_bps / Decimal(10000))
    xrpay_fee = gross_out * (xrpay_fee_bps / Decimal(10000))

    net_out = gross_out - amm_fee - xrpay_fee

    # update pools -----------------------------
    if direction == "COL->XRP":
        pool["base_liq"] += dx
        pool["quote_liq"] -= net_out
    else:
        pool["quote_liq"] += dy
        pool["base_liq"] -= net_out

    # slippage --------------------------------
    mid_before = quote / base
    mid_after = pool["quote_liq"] / pool["base_liq"]
    slippage = abs((mid_after - mid_before) / mid_before)

    return {
        "direction": direction,
        "amount_in": float(amount),
        "amount_out": float(net_out),
        "slippage": float(slippage),
        "lp_fee": float(amm_fee),
        "xrpay_fee": float(xrpay_fee),
        "pool_base_after": float(pool["base_liq"]),
        "pool_quote_after": float(pool["quote_liq"])
    }

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (Full Loop: Tick + Vol + Spread + Swaps)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)
    random.seed(config["simulation"]["random_seed"])

    max_ticks = config["simulation"]["max_ticks"]
    tick_ms = config["tick_interval_ms"]

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    ndjson_path = os.path.join(args.out, f"sim_events_{timestamp}.ndjson")
    summary_path = os.path.join(args.out, f"sim_summary_{timestamp}.json")

    with open(ndjson_path, "w", encoding="utf-8") as log:
        for tick in range(1, max_ticks + 1):

            # --- TICK EVENT ---
            log.write(json.dumps({
                "type": "tick",
                "tick": tick,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }) + "\n")

            # --- VOLATILITY ---
            pool = pools["COL_XRP"]
            base = pool["base_liq"]
            quote = pool["quote_liq"]

            mid_before = quote / base
            mid_after, noise = apply_vol(config, mid_before)
            pool["quote_liq"] = mid_after * base

            log.write(json.dumps({
                "type": "vol_update",
                "tick": tick,
                "mid_before": float(mid_before),
                "mid_after": float(mid_after),
                "noise": float(noise)
            }) + "\n")

            # --- SPREAD ---
            dyn_spread, bid, ask = compute_spread(mid_after, noise=Decimal(str(noise)))
            log.write(json.dumps({
                "type": "spread_update",
                "tick": tick,
                "mid_price": float(mid_after),
                "bid_price": float(bid),
                "ask_price": float(ask),
                "spread_fraction": float(dyn_spread)
            }) + "\n")

            # --- SWAP (AMM INTERACTION) ---
            swap = perform_swap(pool, config)
            if swap:
                swap["type"] = "swap"
                swap["tick"] = tick
                log.write(json.dumps(swap) + "\n")

    # Summary
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "ndjson_file": ndjson_path,
            "max_ticks": max_ticks,
            "tick_interval_ms": tick_ms,
            "seed": config["simulation"]["random_seed"],
            "modules": ["ticks", "volatility", "dynamic_spread", "swaps_enabled"]
        }, f, indent=2)

    print("OK: Full simulation loop with swap events executed.")
    print(f" -> Events:  {ndjson_path}")
    print(f" -> Summary: {summary_path}")
    return 0

if __name__ == "__main__":
    main()
