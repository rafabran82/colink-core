from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

SCHEMA_VERSION = "colink.sim.v1"


@dataclass
class SweepPoint:
    t: int
    price: float
    spread_bps: float
    depth: float


def _read_trades_csv(path: str) -> list[dict]:
    """
    Expected columns (case-insensitive):
      - t (int timestep)
      - side ("buy" or "sell")
      - size (float units)
    Extra columns are ignored. Missing columns are tolerated if headers
    can be mapped case-insensitively; otherwise empty list.
    """
    if not path or not os.path.exists(path):
        return []
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        # case-insensitive map
        columns = {k.lower(): k for k in r.fieldnames or []}
        col_t = columns.get("t")
        col_side = columns.get("side")
        col_size = columns.get("size")
        for raw in r:
            try:
                t = int(raw[col_t]) if col_t else None
                side = str(raw[col_side]).strip().lower() if col_side else ""
                size = float(raw[col_size]) if col_size else 0.0
                if t is None:
                    continue
                if side not in ("buy", "sell"):
                    continue
                if size <= 0:
                    continue
                rows.append({"t": t, "side": side, "size": size})
            except Exception:
                # skip malformed row
                continue
    return rows


def _read_vol_csv(path: str) -> dict[int, float]:
    """
    Expected columns (case-insensitive):
      - t (int timestep)
      - sigma (float multiplier applied to shock stddev at t)
    """
    if not path or not os.path.exists(path):
        return {}
    out: dict[int, float] = {}
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        columns = {k.lower(): k for k in r.fieldnames or []}
        col_t = columns.get("t")
        col_sigma = columns.get("sigma")
        for raw in r:
            try:
                t = int(raw[col_t]) if col_t else None
                sigma = float(raw[col_sigma]) if col_sigma else 1.0
                if t is None:
                    continue
                if sigma <= 0:
                    continue
                out[t] = sigma
            except Exception:
                continue
    return out


def generate_series(
    steps: int,
    seed: int = 42,
    vol_overrides: dict[int, float] | None = None,
    trades: list[dict] | None = None,
) -> list[SweepPoint]:
    random.seed(seed)
    price = 1.0
    depth = 10_000.0
    out: list[SweepPoint] = []

    # base shock sigma; volatility CSV can override per-t
    base_sigma = 0.003
    vol_overrides = vol_overrides or {}
    trades = trades or []

    # Simple “liquidity nudge” from trades: net buys increase price slightly,
    # net sells decrease; very small per-step impact, just to drive the example.
    by_t: dict[int, list[dict]] = {}
    for tr in trades:
        by_t.setdefault(tr["t"], []).append(tr)

    for t in range(steps):
        drift = 0.0005
        sigma = base_sigma * vol_overrides.get(t, 1.0)
        shock = random.gauss(0.0, sigma)
        price = max(0.0001, price * (1.0 + drift + shock))

        # apply net trade impact if any at this timestep
        step_trades = by_t.get(t, [])
        if step_trades:
            net = 0.0
            for tr in step_trades:
                if tr["side"] == "buy":
                    net += tr["size"]
                else:
                    net -= tr["size"]
            # very small price tweak scaled by depth to keep stable
            price *= max(0.0001, 1.0 + 0.00001 * (net / max(depth, 1.0)))

        spread_bps = 10.0 + 8.0 * math.sin(t / 15.0)
        depth = max(100.0, depth * (1.0 + random.uniform(-0.02, 0.02)))
        out.append(SweepPoint(t=t, price=price, spread_bps=spread_bps, depth=depth))
    return out


def save_json(
    points: list[SweepPoint],
    path: str,
    *,
    seed: int,
    pairs: list[str],
    trades_csv: str | None,
    vol_csv: str | None,
) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    d = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "seed": seed,
        "pairs": pairs,
        "inputs": {
            "trades_csv": trades_csv or "",
            "volatility_csv": vol_csv or "",
        },
        "points": [asdict(p) for p in points],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f)


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


def maybe_plot_spread(
    points: list[SweepPoint], png_path: str | None, backend: str, show: bool, hold: bool
) -> None:
    import matplotlib

    if backend:
        matplotlib.use(backend, force=True)
    import matplotlib.pyplot as plt

    xs = [p.t for p in points]
    sp = [p.spread_bps for p in points]

    fig = plt.figure(figsize=(7, 3.5))
    ax = fig.add_subplot(111)
    ax.plot(xs, sp)
    ax.set_xlabel("t")
    ax.set_ylabel("spread_bps")
    ax.set_title("Spread over time")
    ax.grid(True, alpha=0.25)

    fig.tight_layout()
    if png_path:
        os.makedirs(os.path.dirname(png_path) or ".", exist_ok=True)
        fig.savefig(png_path, dpi=120)

    bname = str(matplotlib.get_backend()).lower()
    if show and ("agg" not in bname):
        plt.show(block=hold)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="COLINK Phase 3: sweep + CSV ingest + slippage")
    ap.add_argument("--steps", type=int, default=200, help="number of timesteps")
    ap.add_argument(
        "--pairs", type=str, default="XRP/COL", help="comma-separated pairs, e.g. XRP/COL,COPX/COL"
    )
    ap.add_argument("--seed", type=int, default=42, help="PRNG seed for determinism")
    ap.add_argument("--trades", type=str, default=None, help="CSV path with columns: t,side,size")
    ap.add_argument("--volatility", type=str, default=None, help="CSV path with columns: t,sigma")
    ap.add_argument("--out", type=str, default=None, help="path to write JSON metrics")
    ap.add_argument("--plot", type=str, default=None, help="path to write PNG figure (timeseries)")
    ap.add_argument("--slippage", type=str, default=None, help="path to write slippage PNG")
    ap.add_argument("--spread", type=str, default=None, help="path to write spread-over-time PNG")
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

    # parse inputs
    _pairs = [p.strip() for p in args.pairs.split(",") if p.strip()]
    trades = _read_trades_csv(args.trades) if args.trades else []
    vol_map = _read_vol_csv(args.volatility) if args.volatility else {}

    points = generate_series(args.steps, seed=args.seed, vol_overrides=vol_map, trades=trades)

    if args.out:
        save_json(
            points,
            args.out,
            seed=args.seed,
            pairs=_pairs,
            trades_csv=args.trades,
            vol_csv=args.volatility,
        )
    if args.plot:
        maybe_plot(points, args.plot, backend=backend, show=show, hold=args.hold)
    if args.slippage:
        maybe_plot_slippage(args.slippage, backend=backend, show=show, hold=args.hold)
    if args.spread:
        maybe_plot_spread(points, args.spread, backend=backend, show=show, hold=args.hold)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
