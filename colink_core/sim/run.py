from __future__ import annotations
from .xrpl_snapshot import load_bootstrap_snapshot
from .amm import AMMPool, MetricsEngine, NDJSONLogger
import argparse
import json
import math
import os
import pathlib
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime

def _select_backend(name: str | None) -> str:
    backend = (name or os.getenv("DISPLAY_BACKEND") or "Agg").strip()
    import matplotlib

    if backend.lower() == "agg":
        matplotlib.use("Agg")
    else:
        matplotlib.use(backend)
    return backend

def _git_sha() -> str | None:
    sha = os.getenv("GITHUB_SHA")
    if sha:
        return sha
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        )
        return out.strip()
    except Exception:
        return None

def _demo_series(n: int = 240) -> list[tuple[int, float]]:
    """Generate a simple synthetic series (random-walk over a gentle sine)."""
    series: list[tuple[int, float]] = []
    t0 = time.time()
    val = 0.0
    for i in range(n):
        # jittered sine + bounded random walk
        val += random.uniform(-0.25, 0.25)
        baseline = 2.0 * math.sin(i / 24.0)
        y = baseline + val
        ts_ms = int((t0 + i * 0.05) * 1000)  # 20 Hz-ish
        series.append((ts_ms, y))
    return series
def _amm_series_demo(
    n: int = 240,
    fee_rate: float = 0.003,
) -> list[tuple[int, float]]:
    """
    AMM-backed demo series.

    Uses a simple COPX/COL pool and repeatedly applies swaps to
    generate a time series of prices suitable for plotting.
    """
    pool = AMMPool("COPX", "COL", 1000.0, 7000.0, fee_rate)
    series: list[tuple[int, float]] = []

    t0 = time.time()
    ts = t0

    for i in range(n):
        # Alternate directions for a bit of natural volatility
        if i % 2 == 0:
            pool.swap_a_to_b(50.0)
        else:
            pool.swap_b_to_a(30.0)

        ts_ms = int(ts * 1000)
        price = pool.price_a_to_b
        series.append((ts_ms, price))
        ts += 0.05  # ~20 Hz-ish

    return series

def run_demo(out_prefix: pathlib.Path, display: str | None) -> dict:
    backend = _select_backend(display)
    # Import pyplot only after backend selection
    import matplotlib.pyplot as plt

    series = _demo_series()

    # 1) Plot â†’ PNG
    xs = [t for (t, _y) in series]
    ys = [y for (_t, y) in series]

    # Convert epoch ms to relative seconds for x-axis ticks (keeps it backend-agnostic)
    x0 = xs[0]
    xrel = [(t - x0) / 1000.0 for t in xs]

    plt.figure(figsize=(8, 4.5), dpi=150)
    plt.plot(xrel, ys, linewidth=1.5)
    plt.title("COLINK Simulation Demo")
    plt.xlabel("t (s, relative)")
    plt.ylabel("value")
    plt.grid(True, linestyle="--", alpha=0.4)

    png_path = out_prefix.with_suffix(".png")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(png_path)
    plt.close()

    # 2) NDJSON timeseries
    ndjson_path = out_prefix.with_suffix(".ndjson")
    with ndjson_path.open("w", encoding="utf-8") as f:
        for i, (ts_ms, y) in enumerate(series):
            rec = {"t": ts_ms, "i": i, "value": y}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 3) Metrics summary
    metrics = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "backend": backend,
        "python": platform.python_version(),
        "os": platform.platform(),
        "git_sha": _git_sha(),
        "sample_count": len(series),
        "value_min": min(ys),
        "value_max": max(ys),
        "value_mean": statistics.fmean(ys),
        "value_stdev": statistics.pstdev(ys) if len(ys) > 1 else 0.0,
        "duration_ms": xs[-1] - xs[0] if len(xs) > 1 else 0,
        "labels": {"pair": "DEMO/COL", "env": os.getenv("COLINK_ENV", "dev")},
        "artifacts": {
            "png": str(png_path),
            "ndjson": str(ndjson_path),
        },
    }

    json_path = out_prefix.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    return {
        "png": str(png_path),
        "ndjson": str(ndjson_path),
        "json": str(json_path),
        "backend": backend,
    }

from .engine import run_sim
from dataclasses import dataclass
from typing import Optional

@dataclass
class SimContext:
    out_prefix: pathlib.Path
    display: str | None
    xrpl_snapshot: Optional[object] = None
    swap_direction: str | None = None
    swap_amount: float | None = None

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="COLINK sim runner (PNG + NDJSON + JSON metrics)")

    p.add_argument("--demo", action="store_true", help="Run the demo series generator")

    p.add_argument(
        "--amm-demo",
        action="store_true",
        help="Run the AMM-backed demo series (COPX/COL pool)",
    )

    p.add_argument(
        "--display",
        type=str,
        default=None,
        help="Matplotlib backend (default: env DISPLAY_BACKEND or Agg)",
    )

    p.add_argument(
        "--out-prefix",
        type=str,
        required=True,
        help="Output path prefix (no extension)",
    )

    p.add_argument(
        "--xrpl-bootstrap-dir",
        type=str,
        default=None,
        help=(
            "Optional path to an XRPL bootstrap snapshot directory "
            "(balances/orderbook/bridge_state JSON files)."
        ),
    )

    p.add_argument(
        "--sim",
        action="store_true",
        help="Run the COLINK XRPL simulation engine",
    )

    p.add_argument(
        "--swap-direction",
        type=str,
        default=None,
        help="Swap direction: CPX->COL or COL->CPX",
    )

    p.add_argument(
        "--swap-amount",
        type=float,
        default=None,
        help="Amount input for the swap",
    )

    return p.parse_args(argv)

def run_amm_demo(out_prefix: pathlib.Path, display: str | None) -> dict:
    backend = _select_backend(display)
    # Import pyplot only after backend selection
    import matplotlib.pyplot as plt

    series = _amm_series_demo()

    xs = [t for (t, _y) in series]
    ys = [y for (_t, y) in series]

    # Convert epoch ms to relative seconds for x-axis ticks (keeps it backend-agnostic)
    x0 = xs[0]
    xrel = [(t - x0) / 1000.0 for t in xs]

    plt.figure(figsize=(8, 4.5), dpi=150)
    plt.plot(xrel, ys, linewidth=1.5)
    plt.title("COLINK AMM Demo (COPX/COL)")
    plt.xlabel("t (s, relative)")
    plt.ylabel("price (COL per COPX)")
    plt.grid(True, linestyle="--", alpha=0.4)

    png_path = out_prefix.with_suffix(".png")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(png_path)
    plt.close()

    # 2) NDJSON timeseries
    ndjson_path = out_prefix.with_suffix(".ndjson")
    with ndjson_path.open("w", encoding="utf-8") as f:
        for i, (ts_ms, y) in enumerate(series):
            rec = {"t": ts_ms, "i": i, "value": y}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 3) Metrics summary
    metrics = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "backend": backend,
        "python": platform.python_version(),
        "os": platform.platform(),
        "git_sha": _git_sha(),
        "sample_count": len(series),
        "value_min": min(ys),
        "value_max": max(ys),
        "value_mean": statistics.fmean(ys),
        "value_stdev": statistics.pstdev(ys) if len(ys) > 1 else 0.0,
        "duration_ms": xs[-1] - xs[0] if len(xs) > 1 else 0,
        "labels": {"pair": "COPX/COL", "env": os.getenv("COLINK_ENV", "dev")},
        "artifacts": {
            "png": str(png_path),
            "ndjson": str(ndjson_path),
        },
    }

    json_path = out_prefix.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    return {
        "png": str(png_path),
        "ndjson": str(ndjson_path),
        "json": str(json_path),
        "backend": backend,
    }

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # XRPL bootstrap (read-only wiring)
    xrpl_snapshot = None
    if args.xrpl_bootstrap_dir:
        try:
            xrpl_snapshot = load_bootstrap_snapshot(args.xrpl_bootstrap_dir)
        except Exception as exc:
            print(f"[XRPL] Warning: failed to load snapshot: {exc}")
            xrpl_snapshot = None
    if xrpl_snapshot is not None:
        print(f"[XRPL] Loaded bootstrap snapshot from {xrpl_snapshot.base_dir}")

    # Build unified context
    ctx = SimContext(
        out_prefix=pathlib.Path(args.out_prefix),
        display=args.display,
        xrpl_snapshot=xrpl_snapshot,
        swap_direction=args.swap_direction,
        swap_amount=args.swap_amount,
    )

    if args.amm_demo:
        return run_amm_demo(pathlib.Path(args.out_prefix), args.display)
    if args.demo:
        return run_demo(pathlib.Path(args.out_prefix), args.display)
    print("DEBUG: calling run_sim")

if __name__ == "__main__":
    sys.exit(main())








