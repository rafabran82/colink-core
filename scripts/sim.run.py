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
    return mid * (Decimal(1) + drift + noise)

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (Tick Loop + Volatility)"
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

            # --- Emit tick event ---
            tick_event = {
                "type": "tick",
                "tick": tick,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            log.write(json.dumps(tick_event) + "\n")

            # --- Apply volatility to COL_XRP mid price ---
            pool = pools["COL_XRP"]
            base = pool["base_liq"]
            quote = pool["quote_liq"]

            mid_before = quote / base
            mid_after = apply_vol(config, mid_before)

            # Adjust quote liquidity to preserve ratio
            pool["quote_liq"] = mid_after * base

            vol_event = {
                "type": "vol_update",
                "tick": tick,
                "pool": "COL_XRP",
                "mid_price_before": float(mid_before),
                "mid_price_after": float(mid_after)
            }
            log.write(json.dumps(vol_event) + "\n")

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "events_written": max_ticks * 2,
            "ndjson_file": ndjson_path,
            "tick_interval_ms": tick_ms,
            "seed": config["simulation"]["random_seed"],
            "volatility": config["volatility"],
            "pools_initialized": True
        }, f, indent=2)

    print("OK: Tick loop + volatility updates executed.")
    print(f" -> Events:  {ndjson_path}")
    print(f" -> Summary: {summary_path}")
    return 0

if __name__ == "__main__":
    main()
