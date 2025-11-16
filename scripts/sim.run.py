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

    if direction == "COL->XRP":
        dx = amount
        k = base * quote
        new_base = base + dx
        new_quote = k / new_base
        dy = quote - new_quote
    else:
        dy = amount
        k = base * quote
        new_quote = quote + dy
        new_base = k / new_quote
        dx = base - new_base

    amm_fee_bps = pool["fee_bps"]
    xrpay_fee_bps = Decimal(str(config["fees"]["xrpay_fee_bps"]))

    gross = dy if direction == "COL->XRP" else dx
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
    parser = argparse.ArgumentParser(
        description="COLINK Simulation (Phase 3: Treasury + Accounting Layer)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()
    pools = init_pools(config)
    random.seed(config["simulation"]["random_seed"])

    max_ticks = config["simulation"]["max_ticks"]
    tick_ms = config["tick_interval_ms"]

    # NEW: accounting interval
    acc_interval = config["accounting"]["interval_ticks"]

    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    ndjson_path = os.path.join(args.out, f"sim_events_{timestamp}.ndjson")
    summary_path = os.path.join(args.out, f"sim_summary_{timestamp}.json")

    # --- ACCUMULATORS ---
    lp_fee_accum = Decimal("0")
    xrpay_fee_accum = Decimal("0")
    treasury_balance = Decimal("0")
    total_volume = Decimal("0")
    total_swaps = 0
    total_slippage = Decimal("0")
    min_slip = None
    max_slip = None

    accounting_events = 0

    with open(ndjson_path, "w", encoding="utf-8") as log:
        for tick in range(1, max_ticks + 1):

            # --- TICK ---
            log.write(json.dumps({
                "type": "tick",
                "tick": tick,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }) + "\n")

            pool = pools["COL_XRP"]
            base = pool["base_liq"]
            quote = pool["quote_liq"]

            # --- VOLATILITY ---
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

            # --- SWAP ---
            swap = perform_swap(pool, config)
            if swap:
                total_swaps += 1
                amount = Decimal(str(swap["amount"]))
                lp_fee = Decimal(str(swap["lp_fee"]))
                xrpay_fee = Decimal(str(swap["xrpay_fee"]))
                slippage = Decimal(str(swap["slippage"]))

                total_volume += amount
                lp_fee_accum += lp_fee
                xrpay_fee_accum += xrpay_fee
                treasury_balance += xrpay_fee

                total_slippage += slippage
                min_slip = slippage if min_slip is None else min(min_slip, slippage)
                max_slip = slippage if max_slip is None else max(max_slip, slippage)

                swap["type"] = "swap"
                swap["tick"] = tick
                log.write(json.dumps(swap) + "\n")

            # --- ACCOUNTING EVENT ---
            if tick % acc_interval == 0:
                accounting_events += 1

                est_lp_apy = float(lp_fee_accum) * 365 / (float(total_volume) + 1e-9)
                est_xrpay_apy = float(xrpay_fee_accum) * 365 / (float(total_volume) + 1e-9)

                acc = {
                    "type": "accounting",
                    "tick": tick,
                    "lp_fee_accum": float(lp_fee_accum),
                    "xrpay_fee_accum": float(xrpay_fee_accum),
                    "treasury_balance": float(treasury_balance),
                    "est_lp_apy": est_lp_apy,
                    "est_xrpay_apy": est_xrpay_apy
                }
                log.write(json.dumps(acc) + "\n")

    # SUMMARY -------------------------------------------
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "ndjson_file": ndjson_path,
            "max_ticks": max_ticks,
            "tick_interval_ms": tick_ms,
            "swaps_executed": total_swaps,
            "total_volume": float(total_volume),
            "lp_fee_accum": float(lp_fee_accum),
            "xrpay_fee_accum": float(xrpay_fee_accum),
            "treasury_balance": float(treasury_balance),
            "accounting_events": accounting_events,
            "avg_slippage": float(total_slippage / max(total_swaps, 1)),
            "min_slippage": float(min_slip) if min_slip is not None else 0,
            "max_slippage": float(max_slip) if max_slip is not None else 0,
            "modules": [
                "ticks",
                "volatility",
                "dynamic_spread",
                "swaps_enabled",
                "fee_accumulation",
                "treasury_accounting"
            ]
        }, f, indent=2)

    print("OK: Full simulation loop with treasury + accounting layer executed.")
    print(f" -> Events:  {ndjson_path}")
    print(f" -> Summary: {summary_path}")
    return 0

if __name__ == "__main__":
    main()
