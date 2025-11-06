from __future__ import annotations

import argparse
import csv
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Force headless unless --show is used or SIM_NO_GUI explicitly set to "0"
if os.environ.get("SIM_NO_GUI", "1") != "0":
    matplotlib.use("Agg")  # non-interactive backend

# Local import of the simulator
from .liquidity_sim import LiquiditySim


@dataclass
class Scenario:
    trade: float
    volatility: float


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def run_one_scenario(scn: Scenario, out_dir: Path, steps: int = 500) -> Path:
    """
    Run a single scenario and export a CSV with key metrics each step.
    Returns the CSV path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = _utc_stamp()
    csv_path = out_dir / f"sim_{scn.trade}_{scn.volatility}_{ts}.csv"

    # Simple AMM with fee and initial reserves
    sim = LiquiditySim(reserve_a=100_000.0, reserve_b=100_000.0, fee=0.003)

    # External price shock series (random walk around 1.0)
    rng = np.random.default_rng()
    shocks = rng.normal(loc=0.0, scale=scn.volatility, size=steps).astype(float)
    price = 1.0

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["step", "price", "reserve_a", "reserve_b", "k", "trade_size", "volatility"]
        )
        for i in range(steps):
            price *= float(1.0 + shocks[i])
            # alternate direction each step: A->B on even steps, B->A on odd
            if i % 2 == 0:
                sim.swap_a_to_b(scn.trade)
            else:
                sim.swap_b_to_a(scn.trade)
            k = sim.reserve_a * sim.reserve_b
            writer.writerow([i, price, sim.reserve_a, sim.reserve_b, k, scn.trade, scn.volatility])

    return csv_path


def plot_summary(csv_paths: Iterable[Path], show: bool = False) -> Path:
    """
    Create an overlay plot summarizing k (invariant) drift per scenario.
    Saves summary_overlay.png next to the CSVs and returns the image path.
    """
    csv_paths = list(csv_paths)
    if not csv_paths:
        raise ValueError("No CSV files provided to plot_summary().")

    out_dir = csv_paths[0].parent
    out_img = out_dir / "summary_overlay.png"

    # Parse series
    series: list[tuple[str, np.ndarray, np.ndarray]] = []
    for p in csv_paths:
        steps, ks, trade, vol = [], [], None, None
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                steps.append(int(row["step"]))
                ks.append(float(row["k"]))
                trade = trade or float(row["trade_size"])
                vol = vol or float(row["volatility"])
        label = f"trade={trade:g}, vol={vol:g}"
        series.append((label, np.array(steps, dtype=int), np.array(ks, dtype=float)))

    # Plot
    fig, ax = plt.subplots(figsize=(9, 6), dpi=120)
    for label, x, y in series:
        ax.plot(x, y, label=label, linewidth=1.6)

    ax.set_title("COL/XRP Liquidity â€“ Invariant (k) Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("k = reserve_a * reserve_b")
    ax.grid(True, alpha=0.25)
    ax.legend(title="Scenarios", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_img)

    # Only show if explicitly requested or SIM_NO_GUI=0
    if show or os.environ.get("SIM_NO_GUI", "1") == "0":
        plt.show()
    else:
        plt.close(fig)

    return out_img


# ----- CLI -----
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run COL/XRP liquidity sim sweeps.")
    ap.add_argument(
        "--trades",
        nargs="+",
        required=True,
        type=float,
        help="One or more trade sizes (e.g. --trades 100 500 1000)",
    )
    ap.add_argument(
        "--volatility",
        nargs="+",
        required=True,
        type=float,
        help="One or more volatilities (e.g. --volatility 0.01 0.03)",
    )
    ap.add_argument(
        "--steps",
        type=int,
        default=500,
        help="Steps per scenario (default: 500)",
    )
    ap.add_argument(
        "--show",
        action="store_true",
        help="Show the overlay window (default is headless).",
    )
    ap.add_argument(
        "--outdir",
        type=str,
        default="sim_results",
        help="Directory for CSVs and plot (default: sim_results)",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.outdir)

    # Build scenario grid
    scenarios = [Scenario(t, v) for t in args.trades for v in args.volatility]

    exported: list[Path] = []
    for scn in scenarios:
        print(f"\n=== Running trade={scn.trade}, volatility={scn.volatility} ===")
        path = run_one_scenario(scn, out_dir=out_dir, steps=args.steps)
        print(f"âœ… Exported {path}")
        exported.append(path)

    img = plot_summary(exported, show=args.show)
    print(f"ðŸ“Š Saved overlay summary: {img}")


if __name__ == "__main__":
    main()
