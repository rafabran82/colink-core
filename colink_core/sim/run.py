from __future__ import annotations

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


def run_demo(out_prefix: pathlib.Path, display: str | None) -> dict:
    backend = _select_backend(display)
    # Import pyplot only after backend selection
    import matplotlib.pyplot as plt

    series = _demo_series()

    # 1) Plot → PNG
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="COLINK sim runner (PNG + NDJSON + JSON metrics)")
    p.add_argument("--demo", action="store_true", help="Run the demo series generator")
    p.add_argument(
        "--display",
        type=str,
        default=None,
        help="Matplotlib backend (default: env DISPLAY_BACKEND or Agg)",
    )
    p.add_argument(
        "--out-prefix", type=str, required=True, help="Output path prefix (no extension)"
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_prefix = pathlib.Path(args.out_prefix)
    if args.demo:
        res = run_demo(out_prefix, args.display)
        print(json.dumps({"ok": True, "backend": res["backend"], "prefix": str(out_prefix)}))
        return 0
    print(json.dumps({"ok": False, "error": "no mode selected (try --demo)"}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
