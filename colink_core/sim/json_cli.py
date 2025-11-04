from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Local imports
from .run_sweep import simulate_gbm_paths, plot_paths, plot_hist  # type: ignore


# ---------- quote ----------
def _calc_quote(col_in: float, min_out_bps: float, twap_guard: bool) -> Dict[str, Any]:
    # simple deterministic calc to keep tests stable
    haircut = (min_out_bps / 10_000.0)
    eff = 1.0 - haircut
    copx_out = col_in * eff
    return {
        "col_in": col_in,
        "min_out_bps": min_out_bps,
        "min_out": copx_out,
        "copx_out": copx_out,
        "eff_copx_per_col": eff,
        "twap_guard": bool(twap_guard),
        "raw": {
            "note": "smoke-quote",
            "inputs": {"col_in": col_in, "min_out_bps": min_out_bps, "twap_guard": bool(twap_guard)},
            "calc": {"haircut": haircut},
        },
    }


def cmd_quote(ns: argparse.Namespace) -> None:
    data = _calc_quote(col_in=float(ns.col_in), min_out_bps=float(ns.min_out_bps), twap_guard=bool(ns.twap_guard))
    print(json.dumps(data))


# ---------- sweep ----------
def cmd_sweep(ns: argparse.Namespace) -> None:
    outdir = Path(ns.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # tiny stable sweep: 64 paths, 32 steps
    paths = simulate_gbm_paths(n_paths=64, n_steps=32, s0=1.0, mu=0.0, sigma=0.25, dt=1/32)

    charts: List[str] = []
    p0 = outdir / "sweep_paths-0000.png"
    h0 = outdir / "sweep_hist-0000.png"
    try:
        plot_paths(paths, title="Simulated price paths", outfile=p0.as_posix())
        charts.append(p0.as_posix())
    except Exception:
        pass

    try:
        # Use last-step distribution
        last = [row[-1] for row in paths]
        plot_hist(last, title="Terminal price distribution", outfile=h0.as_posix())
        charts.append(h0.as_posix())
    except Exception:
        pass

    print(json.dumps({"charts": charts}))


# ---------- CLI ----------
def main() -> int:
    import importlib.metadata as md

    parser = argparse.ArgumentParser(prog="colink-json", description="COLINK simulation JSON CLI")
    parser.add_argument("--version", action="store_true", help="print package version and exit")

    sub = parser.add_subparsers(dest="cmd", required=False)

    p_q = sub.add_parser("quote", help="produce a quote JSON")
    p_q.add_argument("--col-in", dest="col_in", required=True, type=float)
    p_q.add_argument("--min-out-bps", dest="min_out_bps", required=True, type=float)
    p_q.add_argument("--twap-guard", dest="twap_guard", action="store_true")
    p_q.set_defaults(func=cmd_quote)

    p_s = sub.add_parser("sweep", help="run small GBM sweep and emit charts JSON")
    p_s.add_argument("--outdir", dest="outdir", required=True, type=str)
    p_s.set_defaults(func=cmd_sweep)

    args = parser.parse_args()

    if args.version:
        try:
            print(md.version("colink-core"))
        except Exception:
            # fallback: unknown version in dev
            print("0.0.0")
        return 0

    # Default to help if no subcommand
    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
