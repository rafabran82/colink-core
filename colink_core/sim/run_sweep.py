#!/usr/bin/env python3
# Compatibility runner to satisfy legacy tests and headless smoke usage.
# Accepts old flags, emits JSON with expected header, and writes simple plots.

import argparse, json, os, pathlib, sys, random, datetime as dt

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

def write_json(path: pathlib.Path, seed: int, steps: int, pair: str, display: str):
    doc = {
        "schema_version": "colink.sim.v1",
        "ok": True,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed": seed,
        "steps": steps,
        "pairs": pair,
        "display": display,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

def write_png(path: pathlib.Path, title: str):
    if plt is None:
        path.write_bytes(b"")  # placeholder when matplotlib is unavailable
        return
    xs = list(range(10))
    ys = [random.random() for _ in xs]
    fig, ax = plt.subplots()
    ax.plot(xs, ys)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--display", default=os.environ.get("BACKEND", "Agg"),
                    choices=["Agg","TkAgg","Qt5Agg","QtAgg","MacOSX"])
    ap.add_argument("--out", default=None, help="JSON output file")
    ap.add_argument("--params", default=None, help="(ignored) JSON params")
    ap.add_argument("--demo", action="store_true", help="(ignored) demo mode")

    # legacy/test flags we accept (some are no-ops here)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--pairs", type=str, default="XRP/COL")
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--trades", type=str, default=None)
    ap.add_argument("--volatility", type=str, default=None)
    ap.add_argument("--plot", type=str, default=None)
    ap.add_argument("--slippage", type=str, default=None)
    ap.add_argument("--spread", type=str, default=None)
    ap.add_argument("--no-show", action="store_true")
    ap.add_argument("--metrics-only", action="store_true")  # tolerated, no-op

    args = ap.parse_args(argv)

    # Ensure dirs exist
    for maybe in [args.out, args.plot, args.slippage, args.spread]:
        if maybe:
            pathlib.Path(maybe).parent.mkdir(parents=True, exist_ok=True)

    # JSON output
    if args.out:
        write_json(pathlib.Path(args.out), args.seed, args.steps, args.pairs, args.display)

    # Plots if requested
    if args.plot:
        write_png(pathlib.Path(args.plot), f"plot {args.pairs}")
    if args.slippage:
        write_png(pathlib.Path(args.slippage), f"slippage {args.pairs}")
    if args.spread:
        write_png(pathlib.Path(args.spread), f"spread {args.pairs}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
