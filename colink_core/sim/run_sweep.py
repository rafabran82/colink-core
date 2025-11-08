# -*- coding: utf-8 -*-
from __future__ import annotations

"""
colink_core.sim.run_sweep

Purpose:
- Run a parameter sweep (or a single run) for COLINK simulations.
- Harden plotting so matplotlib is imported ONLY AFTER the backend is chosen.
- Default backend is 'Agg' for headless CI (no system display required).

Usage examples:
  python -m colink_core.sim.run_sweep --display Agg --out ./.artifacts/last_sweep.png
  python -m colink_core.sim.run_sweep --display TkAgg
"""

import os
import sys
import json
import argparse
from typing import Any, Dict, Optional


def init_matplotlib(backend: str = "Agg"):
    """
    Select matplotlib backend *before* importing pyplot.
    Returns a ready-to-use `plt` object.
    """
    # Set env first so wheels like matplotlib respect it at import time
    os.environ["MPLBACKEND"] = backend

    # Force the backend selection at runtime too (defensive)
    import matplotlib  # noqa: WPS433 (runtime import by design)
    try:
        matplotlib.use(backend, force=True)
    except Exception:
        # If use() complains but an env backend is present, we still proceed.
        pass

    # Import pyplot only after backend is fixed
    import matplotlib.pyplot as plt  # noqa: WPS433 (runtime import by design)

    return plt


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run COLINK simulation sweep.")
    p.add_argument(
        "--display",
        default=os.environ.get("DISPLAY_BACKEND", "Agg"),
        choices=["Agg", "TkAgg", "Qt5Agg", "QtAgg", "MacOSX"],
        help="Matplotlib backend to use (default: Agg for headless CI).",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Optional path to save a summary plot (PNG).",
    )
    p.add_argument(
        "--params",
        default=None,
        help="Optional JSON string or path to JSON file with sweep params.",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Render a small demo plot (useful for CI sanity checks).",
    )
    return p.parse_args(argv)


def load_params(params_arg: Optional[str]) -> Dict[str, Any]:
    """
    Accepts either:
      - a JSON string
      - a path to a JSON file
      - None (returns default)
    """
    if not params_arg:
        return {"sweep": {"example_param": [1, 2, 3]}}

    # If it's a path and exists, read the file
    if os.path.exists(params_arg) and os.path.isfile(params_arg):
        with open(params_arg, "r", encoding="utf-8") as f:
            return json.load(f)

    # Otherwise treat as JSON string
    try:
        return json.loads(params_arg)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in --params: {e}") from e


def run_sweep_logic(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder sweep engine.
    Replace with your real sweep execution and metrics aggregation.
    Returns a dict of results (timeseries or summary metrics).
    """
    # Minimal illustrative output that won't break tests
    # (Keep it lightweight; the plotting path will handle visuals.)
    sweep_vals = params.get("sweep", {}).get("example_param", [1, 2, 3])
    results = {
        "summary": {
            "count": len(sweep_vals),
            "min": min(sweep_vals) if sweep_vals else None,
            "max": max(sweep_vals) if sweep_vals else None,
            "mean": sum(sweep_vals) / len(sweep_vals) if sweep_vals else None,
        },
        "series": [{"x": i, "y": v} for i, v in enumerate(sweep_vals)],
    }
    return results


def render_plot(results: Dict[str, Any], out_path: Optional[str], backend: str) -> None:
    """
    Initialize the chosen backend, then plot.
    """
    plt = init_matplotlib(backend)
    # Import numpy only when plotting (keeps top-level import light)
    import numpy as np  # noqa: WPS433

    # Simple line from results["series"]
    xs = np.array([p["x"] for p in results.get("series", [])], dtype=float)
    ys = np.array([p["y"] for p in results.get("series", [])], dtype=float)

    fig = plt.figure(figsize=(6, 4), dpi=120)
    ax = fig.add_subplot(111)
    ax.plot(xs, ys, marker="o")
    ax.set_title("COLINK Sweep Result")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.3)

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight")
    # Always close to avoid resource warnings in CI
    plt.close(fig)


def render_demo(out_path: Optional[str], backend: str) -> None:
    """
    Minimal demo plot to validate backend + wheels in CI.
    """
    plt = init_matplotlib(backend)

    fig = plt.figure(figsize=(4, 3), dpi=120)
    ax = fig.add_subplot(111)
    ax.plot([0, 1, 2], [0, 1, 0], marker="o")
    ax.set_title("Demo (backend: %s)" % backend)
    ax.grid(True, alpha=0.3)

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    params = load_params(args.params)

    if args.demo:
        render_demo(args.out, args.display)
        return 0

    results = run_sweep_logic(params)

    # Optionally write a compact JSON summary to stdout for CI parsing
    print(json.dumps(results.get("summary", {}), separators=(",", ":")))

    # Only import/plot after backend selection
    if args.out:
        render_plot(results, args.out, args.display)

    return 0


if __name__ == "__main__":
    sys.exit(main())