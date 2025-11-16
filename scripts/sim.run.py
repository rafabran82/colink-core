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
    pool_defs = cfg.get("pools", {})
    for name, p in pool_defs.items():
        pools[name] = {
            "base": p["base"],
            "quote": p["quote"],
            "base_liq": Decimal(str(p["initial_base_liquidity"])),
            "quote_liq": Decimal(str(p["initial_quote_liquidity"])),
            "fee_bps": Decimal(str(p["fee_bps"]))
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
        "gross_out": float(dy),
        "impact": float(price_impact)
    }

def apply_fees(gross_out, amm_fee_bps, xrpay_fee_bps):
    gross = Decimal(str(gross_out))
    amm_fee = gross * (Decimal(amm_fee_bps) / Decimal(10000))
    xrpay_fee = gross * (Decimal(xrpay_fee_bps) / Decimal(10000))
    net = gross - amm_fee - xrpay_fee
    return {
        "gross_out": float(gross),
        "amm_fee": float(amm_fee),
        "xrpay_fee": float(xrpay_fee),
        "net_out": float(net)
    }

def apply_volatility(config, value):
    sigma = Decimal(str(config["volatility"]["sigma"]))
    drift = Decimal(str(config["volatility"]["drift"]))
    noise = Decimal(str(random.gauss(0, float(sigma))))

    new_value = value * (Decimal(1) + drift + noise)
    return float(new_value)

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (AMM + Fees + Volatility)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)

    random.seed(config["simulation"]["random_seed"])

    max_slip = config["slippage_model"]["max_slippage_pct"]
    amm_preview = amm_swap_preview(
        pools["COL_XRP"],
        amount_in=1000,
        max_slippage_pct=max_slip
    )

    fee_preview = apply_fees(
        amm_preview.get("gross_out", 0),
        pools["COL_XRP"]["fee_bps"],
        config["fees"]["xrpay_fee_bps"]
    )

    # NEW: Apply volatility to the net output for demo
    net_out = Decimal(str(fee_preview["net_out"]))
    vol_adj = apply_volatility(config, net_out)

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(args.out, f"sim_vol_preview_{timestamp}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "amm_preview": amm_preview,
            "fee_preview": fee_preview,
            "volatility_adjusted": vol_adj
        }, f, indent=2)

    print(f"OK: Volatility integrated + preview written to:")
    print(f" -> {out_file}")
    return 0

if __name__ == "__main__":
    main()
