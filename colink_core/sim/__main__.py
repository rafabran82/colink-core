from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from .amm import PoolState
from .price_utils import modeled_bps_impact_for_size, route_mid_price_copx_per_col
from .risk_guard import quote_with_slippage, size_aware_twap_guard
from .router import exec_col_to_copx, quote_col_to_copx
from .twap import TWAPOracle


def fmt(n: float) -> str:
    return f"{n:,.6f}"

def seed_pools(
    xrp_copx=(10_000.0, 25_000_000.0, 30),
    col_xrp=(10_000.0,    200_000.0, 30),
):
    # XRP is X, COPX is Y
    pool_x_copx = PoolState(x_reserve=xrp_copx[0], y_reserve=xrp_copx[1], fee_bps=xrp_copx[2])
    # XRP is X, COL is Y  (i.e., 1 XRP ~ 20 COL initially)
    pool_col_x  = PoolState(x_reserve=col_xrp[0],  y_reserve=col_xrp[1],  fee_bps=col_xrp[2])
    return pool_col_x, pool_x_copx

def cmd_quote(args: argparse.Namespace) -> int:
    pool_col_x, pool_x_copx = seed_pools()
    col_in = float(args.col_in)

    # Basic routed quote (no mutation)
    q = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
    print(f"Quote: {fmt(col_in)} COL -> {fmt(q.amount_out)} COPX  | eff={fmt(q.effective_price)} COPX/COL")

    # Optional min-out guard
    if args.min_out_bps is not None:
        gq = quote_with_slippage(pool_col_x, pool_x_copx, col_in, slip_bps=float(args.min_out_bps))
        print(f"  Min-out @{args.min_out_bps} bps: {fmt(gq.min_out)} COPX")

    # Optional TWAP size-aware guard
    if args.twap_guard:
        tw = TWAPOracle(window=args.twap_window)
        mid = route_mid_price_copx_per_col(pool_col_x, pool_x_copx)
        tw.warm([mid] * args.twap_window)
        ok, dev, budget = size_aware_twap_guard(
            pool_col_x, pool_x_copx, tw, col_in,
            base_guard_bps=args.base_bps,
            cushion_bps=args.cushion_bps,
            cap_bps=args.cap_bps,
        )
        verdict = "OK" if ok else "BLOCK"
        print(f"  TWAP guard: dev={dev:.1f} bps  budget={budget:.1f} bps  => {verdict}")
    return 0

def cmd_exec(args: argparse.Namespace) -> int:
    pool_col_x, pool_x_copx = seed_pools()
    col_in = float(args.col_in)

    r = exec_col_to_copx(pool_col_x, pool_x_copx, col_in)
    print(f"Exec:  {fmt(col_in)} COL -> {fmt(r.amount_out)} COPX  | eff={fmt(r.effective_price)} COPX/COL")
    print("New prices:",
          "COL/XRP =", fmt(pool_col_x.y_reserve / pool_col_x.x_reserve),
          "COPX/XRP =", fmt(pool_x_copx.y_reserve / pool_x_copx.x_reserve))
    return 0

def cmd_sweep(args: argparse.Namespace) -> int:
    pool_col_x, pool_x_copx = seed_pools()

    sizes = [float(s) for s in args.sizes] if args.sizes else \
        [100, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000]

    outdir = Path(args.outdir or Path(__file__).resolve().parent / "out")
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = outdir / f"sweep_col_to_copx_{stamp}.csv"

    # Warm TWAP
    tw = TWAPOracle(window=args.twap_window)
    mid0 = route_mid_price_copx_per_col(pool_col_x, pool_x_copx)
    tw.warm([mid0] * args.twap_window)

    rows = []
    for col_in in sizes:
        q = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
        modeled = modeled_bps_impact_for_size(pool_col_x, pool_x_copx, col_in)
        ok, dev, budget = size_aware_twap_guard(
            pool_col_x, pool_x_copx, tw, col_in,
            base_guard_bps=args.base_bps,
            cushion_bps=args.cushion_bps,
            cap_bps=args.cap_bps,
        )
        rows.append({
            "col_in": col_in,
            "copx_out": q.amount_out,
            "eff_copx_per_col": q.effective_price,
            "twap": tw.value(),
            "dev_bps": dev,
            "modeled_bps": modeled,
            "budget_bps": budget,
            "approved": ok,
        })

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Saved CSV -> {csv_path}")

    # Optional charts
    try:
        import matplotlib.pyplot as plt

        xs   = [r["col_in"] for r in rows]
        effs = [r["eff_copx_per_col"] for r in rows]
        tws  = [r["twap"] for r in rows]

        plt.figure()
        plt.plot(xs, effs, marker="o", label="Eff. price (COPX/COL)")
        plt.plot(xs, tws,  marker="x", label="TWAP")
        plt.xlabel("Size (COL)"); plt.ylabel("Price (COPX/COL)")
        plt.title()
        plt.grid(True, alpha=0.3)
        plt.legend()
        p1 = outdir / f"sweep_price_vs_size_{stamp}.png"
        plt.tight_layout()
        plt.savefig()
        plt.close()
        print(f"Saved chart -> {p1}")

        devs   = [r["dev_bps"] for r in rows]
        models = [r["modeled_bps"] for r in rows]
        buds   = [r["budget_bps"] for r in rows]

        plt.figure()
        plt.plot(xs, devs,   marker="o", label="Deviation (bps)")
        plt.plot(xs, models, marker="x", label="Modeled impact (bps)")
        plt.plot(xs, buds,   marker="s", label="Guard budget (bps)")
        plt.xlabel("Size (COL)"); plt.ylabel("Basis points (bps)")
        plt.title()
        plt.grid(True, alpha=0.3)
        plt.legend()
        p2 = outdir / f"sweep_devbps_vs_size_{stamp}.png"
        plt.tight_layout()
        plt.savefig()
        plt.close()
        print(f"Saved chart -> {p2}")
    except Exception as e:
        print("Plotting skipped:", e)

    return 0

def main():
    p = argparse.ArgumentParser(prog="colink-sim", description="COLINK routed AMM simulator (COL ⇄ XRP ⇄ COPX)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_q = sub.add_parser("quote", help="Quote COL→COPX")
    p_q.add_argument("--col-in", type=float, required=True)
    p_q.add_argument("--min-out-bps", type=float, help="Optional min-out slippage bps")
    p_q.add_argument("--twap-guard", action="store_true", help="Enable size-aware TWAP guard")
    p_q.add_argument("--twap-window", type=int, default=8)
    p_q.add_argument("--base-bps", type=float, default=100.0)
    p_q.add_argument("--cushion-bps", type=float, default=150.0)
    p_q.add_argument("--cap-bps", type=float, default=2000.0)
    p_q.set_defaults(func=cmd_quote)

    p_e = sub.add_parser("exec", help="Execute COL→COPX (mutates pools)")
    p_e.add_argument("--col-in", type=float, required=True)
    p_e.set_defaults(func=cmd_exec)

    p_s = sub.add_parser("sweep", help="Sweep size curve and write CSV (+charts)")
    p_s.add_argument("--sizes", nargs="*", type=float, help="Space-separated sizes in COL")
    p_s.add_argument("--twap-window", type=int, default=8)
    p_s.add_argument("--base-bps", type=float, default=100.0)
    p_s.add_argument("--cushion-bps", type=float, default=150.0)
    p_s.add_argument("--cap-bps", type=float, default=2000.0)
    p_s.add_argument("--outdir", type=str, help="Output folder (default: package out/)")
    p_s.set_defaults(func=cmd_sweep)

    args = p.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()













