"""
COLINK Liquidity Simulation Sweeper + Summary Overlay
-----------------------------------------------------
Runs multiple liquidity simulations with variable parameters (trade size, volatility)
and exports results + combined overlay plot.

Usage:
    python -m colink_core.sim.run_sweep --trades 100 500 1000 --volatility 0.01 0.03
"""

import argparse
import csv
import os
from datetime import UTC, datetime

import matplotlib.pyplot as plt

from colink_core.sim.liquidity_sim import LiquiditySimulation, Pool, SimulationConfig


def run_and_export(trade_size: float, volatility: float, outdir: str):
    pool = Pool("COL", "XRP", reserve_a=1_000_000, reserve_b=500_000)
    cfg = SimulationConfig(steps=200, trade_size=trade_size, volatility=volatility)
    sim = LiquiditySimulation(pool, cfg)
    sim.run()

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    fname = f"sim_{trade_size}_{volatility}_{ts}.csv"
    fpath = os.path.join(outdir, fname)

    with open(fpath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "price", "reserve_a", "reserve_b"])
        for i, p in enumerate(sim.history["price"]):
            writer.writerow([i, p, sim.history["reserve_a"][i], sim.history["reserve_b"][i]])

    print(f"✅ Exported {fpath}")
    return fpath


def plot_summary(csv_files):
    plt.figure(figsize=(9, 6))
    for fpath in csv_files:
        label = os.path.basename(fpath).replace("sim_", "").replace(".csv", "")
        steps, prices = [], []
        with open(fpath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                steps.append(int(row["step"]))
                prices.append(float(row["price"]))
        plt.plot(steps, prices, label=label)
    plt.title("COL/XRP Liquidity Simulation Summary")
    plt.xlabel("Step")
    plt.ylabel("Price (B/A)")
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    summary_path = os.path.join(os.path.dirname(csv_files[0]), "summary_overlay.png")
    plt.savefig(summary_path)
    print(f"📊 Saved overlay summary: {summary_path}")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Run multiple COL-XRP liquidity simulations")
    parser.add_argument(
        "--trades",
        type=float,
        nargs="+",
        default=[500],
        help="List of trade sizes to test (default: 500)",
    )
    parser.add_argument(
        "--volatility",
        type=float,
        nargs="+",
        default=[0.02],
        help="List of volatility values to test (default: 0.02)",
    )
    parser.add_argument(
        "--outdir", type=str, default="sim_results", help="Output directory for CSVs"
    )

    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    exported = []
    for t in args.trades:
        for v in args.volatility:
            print(f"\n=== Running trade={t}, volatility={v} ===")
            exported.append(run_and_export(t, v, args.outdir))

    if exported:
        plot_summary(exported)


if __name__ == "__main__":
    main()
