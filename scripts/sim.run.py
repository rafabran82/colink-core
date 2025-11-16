#!/usr/bin/env python3
import argparse
import os
import json
import datetime
import sys
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
    pool_defs = cfg.get("pools", {})

    for name, p in pool_defs.items():
        pools[name] = {
            "base": p["base"],
            "quote": p["quote"],
            "base_liq": Decimal(str(p["initial_base_liquidity"])),
            "quote_liq": Decimal(str(p["initial_quote_liquidity"]))
        }

    return pools

def amm_swap_preview(pool, amount_in, max_slippage_pct):
    x = pool["base_liq"]
    y = pool["quote_liq"]
    dx = Decimal(str(amount_in))

    k = x * y
    new_x = x + dx
    new_y = k / new_x

    dy = y - new_y
    price_impact = dy / y

    if price_impact > Decimal(str(max_slippage_pct)):
        return {
            "allowed": False,
            "reason": "slippage_exceeded",
            "impact": float(price_impact)
        }

    return {
        "allowed": True,
        "amount_in": float(dx),
        "amount_out": float(dy),
        "impact": float(price_impact)
    }

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (config + pools + AMM math foundation)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)

    # AMM preview on COL/XRP for verification
    max_slip = config["slippage_model"]["max_slippage_pct"]
    preview = amm_swap_preview(
        pools["COL_XRP"],
        amount_in=1000,
        max_slippage_pct=max_slip
    )

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(args.out, f"sim_amm_preview_{timestamp}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "config_loaded": True,
            "pools_initialized": True,
            "amm_preview": preview
        }, f, indent=2)

    print(f"OK: AMM math loaded + preview written to:")
    print(f" -> {out_file}")
    return 0

if __name__ == "__main__":
    main()
