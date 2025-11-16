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

# AMM, fee, volatility, spread functions unchanged — preserved

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (Full Loop — Event Foundation)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)

    random.seed(config["simulation"]["random_seed"])
    max_ticks = config["simulation"]["max_ticks"]
    tick_ms = config["tick_interval_ms"]

    # Create output folder + NDJSON log file
    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    ndjson_path = os.path.join(args.out, f"sim_events_{timestamp}.ndjson")
    summary_path = os.path.join(args.out, f"sim_summary_{timestamp}.json")

    # Begin writing NDJSON
    with open(ndjson_path, "w", encoding="utf-8") as log:
        for tick in range(1, max_ticks + 1):
            event = {
                "type": "tick",
                "tick": tick,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            log.write(json.dumps(event) + "\n")

    # Write summary metadata
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "events_written": max_ticks,
            "ndjson_file": ndjson_path,
            "tick_interval_ms": tick_ms,
            "seed": config["simulation"]["random_seed"],
            "pools_initialized": True
        }, f, indent=2)

    print("OK: Event loop baseline executed.")
    print(f" -> Events:  {ndjson_path}")
    print(f" -> Summary: {summary_path}")
    return 0

if __name__ == "__main__":
    main()
