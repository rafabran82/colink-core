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

# (existing AMM, fee, volatility, spread functions unchanged)

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (Preflight Loop Structure)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)
    random.seed(config["simulation"]["random_seed"])

    # NEW: Loop parameters (preflight only)
    max_ticks = config["simulation"]["max_ticks"]
    tick_ms = config["tick_interval_ms"]

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(args.out, f"sim_preflight_{timestamp}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "ready": True,
            "max_ticks": max_ticks,
            "tick_interval_ms": tick_ms,
            "pools_initialized": True,
            "volatility": config["volatility"],
            "fees": config["fees"],
            "seed": config["simulation"]["random_seed"]
        }, f, indent=2)

    print(f"OK: Preflight loop structure initialized:")
    print(f" -> {out_file}")
    return 0

if __name__ == "__main__":
    main()
