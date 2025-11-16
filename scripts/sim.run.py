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
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
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

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (Tick + Vol + Dynamic Spread)"
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

            # Tick event
            log.write(json.dumps({
                "type": "tick",
                "tick": tick,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }) + "\n")

            # --- VOLATILITY UPDATE ---
            pool = pools["COL_XRP"]
            base = pool["base_liq"]
            quote = pool["quote_liq"]

            mid_before = quote / base
            mid_after, noise = apply_vol(config, mid_before)

            pool["quote_liq"] = mid_after * base  # preserve ratio

            log.write(json.dumps({
                "type": "vol_update",
                "tick": tick,
                "mid_before": float(mid_before),
                "mid_after": float(mid_after),
                "noise": float(noise)
            }) + "\n")

            # --- SPREAD UPDATE ---
            dyn_spread, bid, ask = compute_spread(mid_after, noise=Decimal(str(noise)))

            log.write(json.dumps({
                "type": "spread_update",
                "tick": tick,
                "mid_price": float(mid_after),
                "bid_price": float(bid),
                "ask_price": float(ask),
                "spread_fraction": float(dyn_spread)
            }) + "\n")

    # Summary
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "events_written": max_ticks * 3,
            "ndjson_file": ndjson_path,
            "tick_interval_ms": tick_ms,
            "seed": config["simulation"]["random_seed"],
            "modules": ["ticks", "volatility", "dynamic_spread"]
        }, f, indent=2)

    print("OK: Tick loop + volatility + spread evolution executed.")
    print(f" -> Events:  {ndjson_path}")
    print(f" -> Summary: {summary_path}")
    return 0

if __name__ == "__main__":
    main()
