#!/usr/bin/env python3
import argparse
import os
import json
import datetime
import sys

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
    pool_defs = cfg.get("pools", {})

    for name, p in pool_defs.items():
        pools[name] = {
            "base": p["base"],
            "quote": p["quote"],
            "base_liq": float(p["initial_base_liquidity"]),
            "quote_liq": float(p["initial_quote_liquidity"])
        }

    return pools

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (config loader + pool init)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()

    # NEW: Initialize pool structures
    pools = init_pools(config)

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(args.out, f"sim_pools_init_{timestamp}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "config_loaded": True,
            "pools": pools
        }, f, indent=2)

    print(f"OK: Pools initialized and written to:")
    print(f" -> {out_file}")
    return 0

if __name__ == "__main__":
    main()
