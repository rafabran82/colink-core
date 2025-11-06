from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import asdict, dataclass


@dataclass
class SweepPoint:
    t: int
    price: float
    spread_bps: float
    depth: float


def generate_series(steps: int, seed: int = 42) -> list[SweepPoint]:
    random.seed(seed)
    price = 1.0
    depth = 10_000.0
    out: list[SweepPoint] = []
    for t in range(steps):
        drift = 0.0005
        shock = random.gauss(0.0, 0.003)
        price = max(0.0001, price * (1.0 + drift + shock))
        spread_bps = 10.0 + 8.0 * math.sin(t / 15.0)
        depth = max(100.0, depth * (1.0 + random.uniform(-0.02, 0.02)))
        out.append(SweepPoint(t=t, price=price, spread_bps=spread_bps, depth=depth))
    return out


def save_json(points: list[SweepPoint], path: str) -> None:
    d = [asdict(p) for p in points]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"points": d}, f)


def maybe_plot(
    points: list[SweepPoint], png_path: str | None, backend: str, show: bool, hold: bool
) -> None:
    import matplotlib

    if backend:
        matplotlib.use(backend, force=True)
    import matplotlib.pyplot as plt

    xs = [p.t for p in points]
    ys = [p.price for p in points]
    sp = [p.spread_bps for p in points]

    fig = plt.figure(figsize=(8, 4))
    ax1 = fig.add_subplot(111)
    ax1.plot(xs, ys, label="price")
    ax1.set_xlabel("t")
    ax1.set_ylabel("price")
    ax1.grid(True, alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(xs, sp, linestyle="--", label="spread_bps")
    ax2.set_ylabel("spread_bps")

    fig.tight_layout()
    if png_path:
        os.makedirs(os.path.dirname(png_path) or ".", exist_ok=True)
        fig.savefig(png_path, dpi=120)

    bname = str(matplotlib.get_backend()).lower()
    if show and ("agg" not in bname):
        plt.show(block=hold)


def slippage_curve_xy(
    trade_sizes: list[float], x_reserve: float, y_reserve: float
) -> tuple[list[float], list[float]]:
    # Constant-product AMM: x*y = k; price impact vs. input size (buy Y with X)
    xs = []
    impacts_bps = []
    k = x_reserve * y_reserve
    p0 = y_reserve / x_reserve  # spot price
    for dx in trade_sizes:
        if dx <= 0.0:
            continue
        x_new = x_reserve + dx
        y_new = k / x_new
        dy = y_reserve - y_new  # output received (Y sold by pool)
        effective_price = dy / dx if dx > 0 else p0
        impact = (effective_price / p0 - 1.0) * 10_000.0  # bps
        xs.append(dx)
        impacts_bps.append(impact)
    return xs, impacts_bps


def maybe_plot_slippage(png_path: str | None, backend: str, show: bool, hold: bool) -> None:
    import matplotlib

    if backend:
        matplotlib.use(backend, force=True)
    import matplotlib.pyplot as plt
    import numpy as np

    # Simple curve over input sizes (in X units) for an example pool
    x_reserve = 100_000.0
    y_reserve = 100_000.0
    trade_sizes = np.linspace(10, 5000, 50).tolist()
    xs, impacts = slippage_curve_xy(trade_sizes, x_reserve, y_reserve)

    fig = plt.figure(figsize=(7, 4))
    ax = fig.add_subplot(111)
    ax.plot(xs, impacts)
    ax.set_xlabel("input size (X units)")
    ax.set_ylabel("price impact (bps)")
    ax.set_title("Constant-product slippage curve")
    ax.grid(True, alpha=0.25)

    fig.tight_layout()
    if png_path:
        os.makedirs(os.path.dirname(png_path) or ".", exist_ok=True)
        fig.savefig(png_path, dpi=120)

    bname = str(matplotlib.get_backend()).lower()
    if show and ("agg" not in bname):
        plt.show(block=hold)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="COLINK Phase 3: sweep + slippage")
    ap.add_argument("--steps", type=int, default=200, help="number of timesteps")
    ap.add_argument(
        "--pairs", type=str, default="XRP/COL", help="comma-separated pairs, e.g. XRP/COL,COPX/COL"
    )
    ap.add_argument("--out", type=str, default=None, help="path to write JSON metrics")
    ap.add_argument("--plot", type=str, default=None, help="path to write PNG figure (timeseries)")
    ap.add_argument("--slippage", type=str, default=None, help="path to write slippage PNG")
    ap.add_argument(
        "--display", type=str, default=None, help="matplotlib backend, e.g., Agg or TkAgg"
    )
    ap.add_argument("--no-show", action="store_true", help="do not call plt.show (default)")
    ap.add_argument(
        "--hold", action="store_true", help="if showing interactively, block until closed"
    )
    args = ap.parse_args(argv)

    backend = args.display or os.environ.get("MPLBACKEND") or "Agg"
    show = not args.no_show

    # NOTE: pairs are accepted and may drive future multi-pair logic; for now we log them
    _pairs = [p.strip() for p in args.pairs.split(",") if p.strip()]

    points = generate_series(args.steps)

    if args.out:
        save_json(points, args.out)
    if args.plot:
        maybe_plot(points, args.plot, backend=backend, show=show, hold=args.hold)
    if args.slippage:
        maybe_plot_slippage(args.slippage, backend=backend, show=show, hold=args.hold)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
