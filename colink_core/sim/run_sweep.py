from __future__ import annotations

import argparse
import csv
import os
import random
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import pstdev

import matplotlib  # backend chosen below (TkAgg/Agg), safely

with suppress(Exception):
    # GUI only if SIM_NO_GUI=0, else headless
    want_gui = os.environ.get("SIM_NO_GUI", "1") == "0"
    matplotlib.use("TkAgg" if want_gui else "Agg", force=True)

from .liquidity_sim import LiquiditySim  # x*y=k AMM

# ---------- helpers ----------


def _ts_utc() -> str:
    # timezone-aware (no deprecation warning)
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _label(trade: float, vol: float) -> str:
    return f"{vol:.02f} | {trade:.1f}"


@dataclass
class ScenarioResult:
    trade: float
    vol: float
    steps: int
    csv_path: Path
    prices: list[float]
    k_series: list[float]
    fees_a_in: float
    fees_b_in: float


# ---------- simulation ----------


def run_single_scenario(
    trade: float,
    vol: float,
    steps: int,
    seed: int | None,
    outdir: Path,
    reserves_a: float = 100_000.0,
    reserves_b: float = 100_000.0,
    fee: float = 0.003,
) -> ScenarioResult:
    if seed is not None:
        # mix in params for deterministic-but-unique streams per scenario
        random.seed(seed ^ int(trade * 1000) ^ int(vol * 1e6) ^ steps)

    sim = LiquiditySim(reserve_a=reserves_a, reserve_b=reserves_b, fee=fee)

    prices: list[float] = []
    k_series: list[float] = []
    fees_a_in = 0.0
    fees_b_in = 0.0

    for _ in range(steps):
        prices.append(sim.price_a_in_b())
        k_series.append(sim.reserve_a * sim.reserve_b)

        # positive size with volatility noise
        size = trade * max(0.1, 1.0 + vol * random.gauss(0.0, 1.0))
        if random.random() < 0.5:
            # A -> B (fee collected in A)
            gross_in = size
            net_in = size * (1.0 - sim.fee)
            fees_a_in += gross_in - net_in
            sim.swap_a_to_b(gross_in)
        else:
            # B -> A (fee collected in B)
            gross_in = size
            net_in = size * (1.0 - sim.fee)
            fees_b_in += gross_in - net_in
            sim.swap_b_to_a(gross_in)

    # terminal snapshot
    prices.append(sim.price_a_in_b())
    k_series.append(sim.reserve_a * sim.reserve_b)

    _ensure_dir(outdir)
    csv_path = outdir / f"sim_{trade}_{vol}_{_ts_utc()}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "price_B_per_A", "k_invariant"])
        for i, (p, k) in enumerate(zip(prices, k_series, strict=False)):
            w.writerow([i, f"{p:.8f}", f"{k:.8f}"])
    print(f"OK Exported {csv_path.as_posix()}")

    return ScenarioResult(
        trade=trade,
        vol=vol,
        steps=steps,
        csv_path=csv_path,
        prices=prices,
        k_series=k_series,
        fees_a_in=fees_a_in,
        fees_b_in=fees_b_in,
    )


def _metrics(sr: ScenarioResult) -> dict:
    # realized vol on simple returns
    rets: list[float] = []
    for i in range(1, len(sr.prices)):
        prev = sr.prices[i - 1]
        if prev > 0.0:
            rets.append((sr.prices[i] - prev) / prev)
    realized_vol = pstdev(rets) if rets else 0.0

    k0 = sr.k_series[0] if sr.k_series else 0.0
    max_dev = max((abs(k - k0) / k0 for k in sr.k_series), default=0.0) if k0 > 0 else 0.0

    return {
        "trade": sr.trade,
        "vol": sr.vol,
        "steps": sr.steps,
        "price_first": sr.prices[0] if sr.prices else float("nan"),
        "price_last": sr.prices[-1] if sr.prices else float("nan"),
        "price_min": min(sr.prices) if sr.prices else float("nan"),
        "price_max": max(sr.prices) if sr.prices else float("nan"),
        "price_drift": (sr.prices[-1] - sr.prices[0]) if len(sr.prices) > 1 else 0.0,
        "realized_vol": realized_vol,
        "fees_a_in": sr.fees_a_in,
        "fees_b_in": sr.fees_b_in,
        "invariant_max_rel_dev": max_dev,
        "csv": sr.csv_path.as_posix(),
    }


# ---------- plotting ----------


def plot_summary(results: list[ScenarioResult], outdir: Path, plot: str, show: bool) -> Path:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 6))

    def pick_series(sr: ScenarioResult) -> tuple[list[int], list[float], str, str]:
        xs = list(range(len(sr.prices)))
        if plot == "price":
            ys = sr.prices
            ylab = "Price (B/A)"
            title = "COL/XRP Liquidity - Price Over Time"
        else:
            ys = sr.k_series
            ylab = "k = reserve_a * reserve_b"
            title = "COL/XRP Liquidity - Invariant (k) Over Time"
        return xs, ys, ylab, title

    trades = sorted({sr.trade for sr in results})
    linestyles = {t: s for t, s in zip(trades, ["-", "--", "-.", ":"] * 4, strict=False)}

    title = "Overlay"
    ylab = ""
    for sr in sorted(results, key=lambda s: (s.vol, s.trade)):
        x, y, ylab, title = pick_series(sr)
        ax.plot(
            x,
            y,
            label=_label(sr.trade, sr.vol),
            linewidth=1.6,
            linestyle=linestyles.get(sr.trade, "-"),
        )

    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel(ylab)
    ax.grid(True, alpha=0.25)
    leg = ax.legend(title="vol | trade", loc="best", frameon=True)
    if leg and leg.get_frame():
        leg.get_frame().set_alpha(0.9)

    out_img = outdir / "summary_overlay.png"
    fig.tight_layout()
    fig.savefig(out_img, dpi=140)

    if show:
        with suppress(Exception):
            plt.show(block=False)
            plt.pause(0.001)
    else:
        plt.close(fig)

    print(f"Saved overlay summary: {out_img.as_posix()}")
    return out_img


# ---------- CLI ----------


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Run COL/XRP liquidity sim sweeps and export CSV/PNG/metrics."
    )
    ap.add_argument(
        "--trades", nargs="+", type=float, required=True, help="Trade sizes (e.g. 100 500 1000)"
    )
    ap.add_argument(
        "--volatility",
        nargs="+",
        type=float,
        required=True,
        help="Volatility scales (e.g. 0.01 0.03)",
    )
    ap.add_argument("--steps", type=int, default=200, help="Steps per scenario (default: 200)")
    ap.add_argument("--seed", type=int, default=None, help="Base RNG seed (optional)")
    ap.add_argument(
        "--outdir", type=str, default="sim_results", help="Output directory (default: sim_results)"
    )
    ap.add_argument(
        "--plot", choices=["price", "k", "both"], default="k", help="Overlay series (default: k)"
    )
    ap.add_argument("--show", action="store_true", help="Try to show a GUI window (non-blocking)")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    _ensure_dir(outdir)

    results: list[ScenarioResult] = []
    for t in args.trades:
        for v in args.volatility:
            results.append(
                run_single_scenario(trade=t, vol=v, steps=args.steps, seed=args.seed, outdir=outdir)
            )

    # metrics.csv (append or create)
    metrics_path = outdir / "metrics.csv"
    headers = [
        "trade",
        "vol",
        "steps",
        "price_first",
        "price_last",
        "price_min",
        "price_max",
        "price_drift",
        "realized_vol",
        "fees_a_in",
        "fees_b_in",
        "invariant_max_rel_dev",
        "csv",
    ]
    rows = [_metrics(sr) for sr in results]
    write_header = not metrics_path.exists()
    with metrics_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow(r)

    # if "both", just plot k for now (keeps single axis simple)
    plot_choice = "k" if args.plot == "both" else args.plot
    plot_summary(results, outdir=outdir, plot=plot_choice, show=args.show)


if __name__ == "__main__":
    main()
