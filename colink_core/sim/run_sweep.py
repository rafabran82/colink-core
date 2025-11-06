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
        # tiny random walk on price
        drift = 0.0005
        shock = random.gauss(0.0, 0.003)
        price = max(0.0001, price * (1.0 + drift + shock))
        # spread oscillates in a band (in bps)
        spread_bps = 10.0 + 8.0 * math.sin(t / 15.0)
        # depth wiggles
        depth = max(100.0, depth * (1.0 + random.uniform(-0.02, 0.02)))
        out.append(SweepPoint(t=t, price=price, spread_bps=spread_bps, depth=depth))
    return out


def save_json(points: list[SweepPoint], path: str) -> None:
    d = [asdict(p) for p in points]
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
        fig.savefig(png_path, dpi=120)

    bname = str(matplotlib.get_backend()).lower()
    if show and ("agg" not in bname):
        plt.show(block=hold)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="COLINK Phase 3: simple sweep stub")
    ap.add_argument("--steps", type=int, default=200, help="number of timesteps")
    ap.add_argument("--out", type=str, default=None, help="path to write JSON metrics")
    ap.add_argument("--plot", type=str, default=None, help="path to write PNG figure")
    ap.add_argument(
        "--display", type=str, default=None, help="matplotlib backend, e.g., Agg or TkAgg"
    )
    ap.add_argument("--no-show", action="store_true", help="do not call plt.show (default)")
    ap.add_argument(
        "--hold", action="store_true", help="if showing interactively, hold (block) until closed"
    )
    args = ap.parse_args(argv)

    # Default display to Agg if neither arg nor env is provided
    backend = args.display or os.environ.get("MPLBACKEND") or "Agg"
    show = not args.no_show
    points = generate_series(args.steps)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        save_json(points, args.out)

    if args.plot:
        os.makedirs(os.path.dirname(args.plot) or ".", exist_ok=True)
        maybe_plot(points, args.plot, backend=backend, show=show, hold=args.hold)

    # If user asked to show but backend is Agg, suppress show to avoid warnings
    if show and (backend.lower().find("agg") >= 0):
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
