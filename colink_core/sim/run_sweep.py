from __future__ import annotations

import argparse
import csv
import os
import random
from contextlib import suppress
from datetime import datetime
from pathlib import Path

import matplotlib

from .liquidity_sim import LiquiditySim


def _get_pyplot(show: bool):
    """
    Choose a Matplotlib backend based on --show or SIM_NO_GUI.
    Headless (Agg) by default; TkAgg when an interactive window is desired.
    """
    want_gui = bool(show) or os.environ.get("SIM_NO_GUI", "1") == "0"
    with suppress(Exception):
        matplotlib.use("TkAgg" if want_gui else "Agg", force=True)
    import matplotlib.pyplot as plt  # imported after backend selection

    return plt


def _safe_ts() -> str:
    # naive UTC timestamp (no tz deps)
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def run_scenario(trade: float, vol: float, steps: int = 200) -> str:
    """
    Run a simple x*y=k AMM simulation and export (step,k) to CSV.
    trade: base trade size (in token A units); B-side uses spot conversion.
    vol:   +/- fractional noise applied to trade size per step (e.g., 0.03 = ±3%).
    """
    sim = LiquiditySim(100_000.0, 100_000.0, fee=0.003)

    rows = []
    rows.append({"step": 0, "k": sim.reserve_a * sim.reserve_b})

    for i in range(1, steps + 1):
        amt_a = trade * (1.0 + random.uniform(-vol, vol))
        if i % 2 == 0:
            # A -> B
            sim.swap_a_to_b(amt_a)
        else:
            # B -> A (convert A-sized notionals to B using spot)
            amt_b = amt_a * sim.price_a_in_b()
            sim.swap_b_to_a(amt_b)
        rows.append({"step": i, "k": sim.reserve_a * sim.reserve_b})

    outdir = Path("sim_results")
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"sim_{trade}_{vol}_{_safe_ts()}.csv"

    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["step", "k"])
        w.writeheader()
        w.writerows(rows)

    return str(out)


def _read_series(csv_path: str) -> tuple[list[int], list[float]]:
    xs: list[int] = []
    ys: list[float] = []
    with open(csv_path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            xs.append(int(row["step"]))
            ys.append(float(row["k"]))
    return xs, ys


def plot_summary(paths: list[str], show: bool = False) -> str:
    """
    Overlay (step,k) series from many CSVs. Save PNG and optionally show().
    Legend key is "vol | trade" derived from the filename pattern: sim_{trade}_{vol}_{ts}.csv
    """
    plt = _get_pyplot(show)
    fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=140)

    # simple style maps
    linestyles = ["-", "--", "-.", ":"]
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]

    for idx, p in enumerate(paths):
        xs, ys = _read_series(p)
        stem = Path(p).stem  # sim_{trade}_{vol}_{ts}
        parts = stem.split("_")
        trade = parts[1] if len(parts) > 1 else "?"
        vol = parts[2] if len(parts) > 2 else "?"
        label = f"{vol} | {trade}"

        ax.plot(
            xs,
            ys,
            label=label,
            linewidth=1.6,
            linestyle=linestyles[idx % len(linestyles)],
            color=colors[idx % len(colors)],
        )

    ax.set_title("COL/XRP Liquidity - Invariant (k) Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("k = reserve_a * reserve_b")
    ax.grid(True, alpha=0.25)
    ax.legend(title="vol | trade", loc="best")
    fig.tight_layout()

    outdir = Path("sim_results")
    outdir.mkdir(parents=True, exist_ok=True)
    out_img = outdir / "summary_overlay.png"
    fig.savefig(out_img, dpi=140)

    if show:
        with suppress(Exception):
            plt.show()
    else:
        plt.close(fig)

    return str(out_img)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run COL/XRP liquidity sim sweeps.")
    ap.add_argument(
        "--trades", nargs="+", type=float, required=True, help="List of trade sizes (A-units)."
    )
    ap.add_argument(
        "--volatility",
        nargs="+",
        type=float,
        required=True,
        help="List of fractional vols (e.g., 0.03).",
    )
    ap.add_argument("--show", action="store_true", help="Display an interactive overlay window.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    exported: list[str] = []

    for t in args.trades:
        for v in args.volatility:
            path = run_scenario(trade=t, vol=v, steps=200)
            exported.append(path)
            print(f"OK Exported {path}")

    out_img = plot_summary(exported, show=args.show)
    print(f"Saved overlay summary: {out_img}")


if __name__ == "__main__":
    main()
