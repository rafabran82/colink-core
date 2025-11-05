from __future__ import annotations

import csv
from copy import deepcopy

from amm import PoolState
from router import exec_col_to_copx, quote_col_to_copx, quote_copx_to_col


def fmt(n):
    return f"{n:,.6f}"


def seed_pools():
    # Pool B: XRP⇄COPX (as before) — 1 XRP ~ 2,500 COPX
    pool_x_copx = PoolState(x_reserve=10_000.0, y_reserve=25_000_000.0, fee_bps=30)

    # Pool A: COL⇄XRP. Interpret XRP as X, COL as Y.
    # Example: 1 XRP ~ 20 COL  (=> 0.05 XRP per COL)
    pool_col_x = PoolState(x_reserve=10_000.0, y_reserve=200_000.0, fee_bps=30)

    return pool_col_x, pool_x_copx


def slippage_sweep(pool_col_x, pool_x_copx, col_sizes):
    rows = []
    for col_in in col_sizes:
        r = quote_col_to_copx(pool_col_x, pool_x_copx, col_in)
        rows.append(
            {
                "col_in": col_in,
                "xrp_intermediate": r.hop1_out,
                "copx_out": r.amount_out,
                "eff_price_copx_per_col": r.effective_price,
            }
        )
    return rows


def main():
    pool_col_x, pool_x_copx = seed_pools()
    print("== Seed ==")
    print("Pool COL⇄XRP: price (COL per XRP):", fmt(pool_col_x.y_reserve / pool_col_x.x_reserve))
    print(
        "Pool XRP⇄COPX: price (COPX per XRP):", fmt(pool_x_copx.y_reserve / pool_x_copx.x_reserve)
    )
    print()

    # Quotes (no mutation)
    q1 = quote_col_to_copx(pool_col_x, pool_x_copx, 5_000.0)
    print("Quote: 5,000 COL -> COPX")
    print(
        "  XRP hop:",
        fmt(q1.hop1_out),
        " COPX out:",
        fmt(q1.amount_out),
        " eff COPX/COL:",
        fmt(q1.effective_price),
    )
    print()

    q2 = quote_copx_to_col(pool_col_x, pool_x_copx, 500_000.0)
    print("Quote: 500,000 COPX -> COL")
    print(
        "  XRP hop:",
        fmt(q2.hop1_out),
        " COL out:",
        fmt(q2.amount_out),
        " eff COL/COPX:",
        fmt(q2.effective_price),
    )
    print()

    # Execute a route (mutates pools)
    poolA = deepcopy(pool_col_x)
    poolB = deepcopy(pool_x_copx)
    r_exec = exec_col_to_copx(poolA, poolB, 10_000.0)
    print("EXECUTE: 10,000 COL → COPX")
    print(
        "  XRP hop:",
        fmt(r_exec.hop1_out),
        " COPX out:",
        fmt(r_exec.amount_out),
        " eff COPX/COL:",
        fmt(r_exec.effective_price),
    )
    print(
        "  New prices:",
        "COL/XRP =",
        fmt(poolA.y_reserve / poolA.x_reserve),
        "COPX/XRP =",
        fmt(poolB.y_reserve / poolB.x_reserve),
    )
    print()

    # Slippage sweep and CSV
    sizes = [100, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000]
    rows = slippage_sweep(pool_col_x, pool_x_copx, sizes)
    out = "swaps.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Saved slippage table → {out}")
    for r in rows:
        print(
            f"  COL_in={fmt(r['col_in'])}  -> COPX_out={fmt(r['copx_out'])}  (eff {fmt(r['eff_price_copx_per_col'])} COPX/COL)"
        )


if __name__ == "__main__":
    main()
