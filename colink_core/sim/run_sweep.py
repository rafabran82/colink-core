from __future__ import annotations
import csv

from amm import PoolState
from router import quote_col_to_copx
from twap import TWAPOracle
from price_utils import (
    route_mid_price_copx_per_col,
    bps_deviation,
    modeled_bps_impact_for_size,
)
from risk_guard import size_aware_twap_guard

def fmt(n: float) -> str:
    return f"{n:,.6f}"

def seed():
    # Pool B: XRP⇄COPX — ~2,500 COPX/XRP
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)
    # Pool A: COL⇄XRP — ~20 COL/XRP  (so ~125 COPX/COL mid-route)
    pool_col_x  = PoolState(x_reserve=10_000.0, y_reserve=200_000.0,   fee_bps=30)
    return pool_col_x, pool_x_copx

def main():
    pool_col_x, pool_x_copx = seed()

    # TWAP over mid-route price; warm with a few identical mids just to init
    twap = TWAPOracle(window=8)
    mid0 = route_mid_price_copx_per_col(pool_col_x, pool_x_copx)
    twap.warm([mid0] * 8)
    print("TWAP warmed. Initial TWAP =", fmt(twap.value()), " COPX/COL")
    print()

    sizes = [100, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000]
    rows = []

    for col_in in sizes:
        q = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
        eff = q.effective_price
        tw  = twap.value()

        dev_bps = bps_deviation(eff, tw)
        # **FIX**: pass both pools + size
        modeled = modeled_bps_impact_for_size(pool_col_x, pool_x_copx, col_in)

        ok, _dev, budget = size_aware_twap_guard(
            pool_col_x, pool_x_copx, twap, col_in,
            base_guard_bps=100.0, cushion_bps=150.0, cap_bps=2000.0
        )

        rows.append({
            "col_in": col_in,
            "quote_copx_out": q.amount_out,
            "eff_px_copx_per_col": eff,
            "twap_copx_per_col": tw,
            "dev_bps_vs_twap": dev_bps,
            "modeled_impact_bps": modeled,
            "guard_budget_bps": budget,
            "approved": int(ok),
        })

        print(
            f"Size={fmt(col_in)} COL | eff={fmt(eff)}  TWAP={fmt(tw)}  "
            f"dev={dev_bps:.1f} bps  modeled={modeled:.1f} bps  "
            f"budget={budget:.1f} bps  => {'OK' if ok else 'BLOCKED'}"
        )

    # CSV
    out_csv = "sweep_col_to_copx.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nSaved CSV → {out_csv}")

    # Charts (optional)
    try:
        import matplotlib.pyplot as plt

        xs   = [r["col_in"] for r in rows]
        effs = [r["eff_px_copx_per_col"] for r in rows]
        tws  = [r["twap_copx_per_col"] for r in rows]

        plt.figure()
        plt.plot(xs, effs, marker="o", label="Eff price (COPX/COL)")
        plt.plot(xs, tws,  marker="o", label="TWAP (COPX/COL)")
        plt.xlabel("COL size")
        plt.ylabel("Price (COPX per COL)")
        plt.title("Price vs Size")
        plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
        plt.savefig("sweep_price_vs_size.png"); plt.close()
        print("Saved chart → sweep_price_vs_size.png")

        devs    = [r["dev_bps_vs_twap"] for r in rows]
        modeled = [r["modeled_impact_bps"] for r in rows]
        budget  = [r["guard_budget_bps"] for r in rows]

        plt.figure()
        plt.plot(xs, devs,    marker="o", label="Deviation vs TWAP (bps)")
        plt.plot(xs, modeled, marker="o", label="Modeled impact (bps)")
        plt.plot(xs, budget,  marker="o", label="Guard budget (bps)")
        plt.xlabel("COL size")
        plt.ylabel("Basis points (bps)")
        plt.title("Deviation vs Size & Guard Budget")
        plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
        plt.savefig("sweep_devbps_vs_size.png"); plt.close()
        print("Saved chart → sweep_devbps_vs_size.png")

    except Exception as e:
        print("Plotting skipped (matplotlib not available):", e)

if __name__ == "__main__":
    main()

