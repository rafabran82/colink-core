from __future__ import annotations

import argparse
import csv
import os
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .liquidity_sim import LiquiditySim


def _utc_ts() -> str:
    # ISO-like compact UTC timestamp
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


@dataclass
class Scenario:
    trade_size: float
    volatility: float


def _ensure_outdir(p: str | Path) -> Path:
    out = Path(p)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _simulate_and_export(trade: float, vol: float, steps: int, outdir: Path) -> Path:
    # Simple constant-product AMM demo
    sim = LiquiditySim(reserve_a=10_000.0, reserve_b=10_000.0, fee=0.003)

    rows: list[tuple[int, float, float, float]] = []
    for i in range(steps):
        # Alternate directions with a tiny random-ish wobble derived from vol.
        amt = trade
        if (i % 2) == 0:
            sim.swap_a_to_b(amt)
        else:
            sim.swap_b_to_a(amt)

        price = sim.price_a_in_b()
        k = sim.reserve_a * sim.reserve_b
        rows.append((i, sim.reserve_a, sim.reserve_b, price * k))  # price*k is just a proxy

    fname = outdir / f"sim_{trade}_{vol}_{_utc_ts()}.csv"
    with fname.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "reserve_a", "reserve_b", "metric"])
        w.writerows(rows)
    print(f"OK Exported {fname.as_posix()}")
    return fname


def _load_series(path: Path) -> tuple[list[int], list[float]]:
    xs: list[int] = []
    ys: list[float] = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                xs.append(int(row["step"]))
                ys.append(float(row["metric"]))
            except Exception:
                # Skip malformed rows
                pass
    return xs, ys


def plot_summary(files: list[Path], outdir: Path, show: bool, hold: bool, which: str) -> Path:
    # Backend selection: GUI only if show requested or SIM_NO_GUI="0"
    want_gui = bool(show) or os.environ.get("SIM_NO_GUI", "1") == "0"
    with suppress(Exception):
        import matplotlib

        matplotlib.use("TkAgg" if want_gui else "Agg", force=True)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10.5, 6.0))

    for p in files:
        x, y = _load_series(p)
        label = p.stem  # file name without extension
        ax.plot(x, y, label=label, linewidth=1.6)

    title = "COL/XRP Liquidity - Invariant proxy over time"
    if which == "price":
        title = "COL/XRP Liquidity - Price proxy over time"
    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel("metric (demo)")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)

    out_img = outdir / "summary_overlay.png"
    fig.tight_layout()
    fig.savefig(out_img, dpi=140)

    if show:
        if hold:
            with suppress(Exception), suppress(KeyboardInterrupt):
                plt.show()
        else:
            with suppress(Exception):
                plt.show(block=False)
                plt.pause(0.001)
    else:
        with suppress(Exception):
            plt.close(fig)

    return out_img


# ----- CLI -----
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run COL/XRP liquidity sim sweeps.")
    ap.add_argument(
        "--trades",
        nargs="+",
        type=float,
        required=True,
        help="One or more trade sizes (e.g. 100 500 1000)",
    )
    ap.add_argument(
        "--volatility",
        nargs="+",
        type=float,
        required=True,
        help="One or more vols (e.g. 0.01 0.03)",
    )
    ap.add_argument(
        "--steps",
        type=int,
        default=200,
        help="Simulation steps per scenario (default: 200)",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="(Reserved) RNG seed for future stochastic logic.",
    )
    ap.add_argument(
        "--outdir",
        type=str,
        default="sim_results",
        help='Output directory (default: "sim_results")',
    )
    ap.add_argument(
        "--plot",
        choices=["price", "k", "both"],
        default="k",
        help='Metric focus for title/legend (default: "k")',
    )
    ap.add_argument(
        "--show",
        action="store_true",
        help="Open a chart window (non-blocking by default).",
    )
    ap.add_argument(
        "--hold",
        action="store_true",
        help="When used with --show, keep the window open (blocking plt.show()).",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    outdir = _ensure_outdir(args.outdir)

    exported: list[Path] = []
    for t in args.trades:
        for v in args.volatility:
            path = _simulate_and_export(trade=t, vol=v, steps=args.steps, outdir=outdir)
            exported.append(path)

    out_img = plot_summary(
        files=exported,
        outdir=outdir,
        show=args.show,
        hold=args.hold,
        which=args.plot,
    )
    print(f"Saved overlay summary: {out_img.as_posix()}")


if __name__ == "__main__":
    main()
