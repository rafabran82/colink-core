from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

# Force a headless-safe backend before any pyplot import.
try:
    import matplotlib  # type: ignore

    matplotlib.use("Agg")
except Exception:
    pass

# Local sim/plot helpers (self-contained, no legacy amm dep)
from .run_sweep import simulate_gbm_paths, plot_paths, plot_hist  # type: ignore


def _print(obj) -> None:
    sys.stdout.write(json.dumps(obj))
    sys.stdout.write("\n")
    sys.stdout.flush()


def cmd_quote(args: argparse.Namespace) -> None:
    col_in = float(getattr(args, "col_in", 8000.0))
    min_out_bps = float(getattr(args, "min_out_bps", 150.0))
    twap_guard = bool(getattr(args, "twap_guard", True))

    haircut = min_out_bps / 10_000.0
    eff = 1.0 - haircut
    copx_out = col_in * eff

    out = {
        "col_in": col_in,
        "min_out_bps": min_out_bps,
        "min_out": copx_out,
        "copx_out": copx_out,
        "eff_copx_per_col": eff,
        "twap_guard": twap_guard,
        "raw": {
            "note": "smoke-quote",
            "inputs": {"col_in": col_in, "min_out_bps": min_out_bps, "twap_guard": twap_guard},
            "calc": {"haircut": haircut},
        },
    }
    _print(out)


def cmd_sweep(args: argparse.Namespace) -> None:
    # All plotting happens headless
    backend = None
    try:
        import matplotlib  # type: ignore

        backend = getattr(matplotlib, "get_backend", lambda: None)()
    except Exception:
        backend = "unknown"

    outdir = os.fspath(getattr(args, "outdir", "charts"))
    os.makedirs(outdir, exist_ok=True)

    # Accept both --n-steps and --steps (alias)
    n_steps = int(getattr(args, "n_steps", 240))
    n_paths = int(getattr(args, "n_paths", 200))
    dt = float(getattr(args, "dt", 1.0 / 240.0))
    mu = float(getattr(args, "mu", 0.0))
    sigma = float(getattr(args, "sigma", 0.2))
    s0 = float(getattr(args, "s0", 1.0))
    seed = getattr(args, "seed", None)
    seed_i = int(seed) if seed is not None else None

    charts: List[str] = []
    try:
        paths = simulate_gbm_paths(
            n_steps=n_steps,
            n_paths=n_paths,
            dt=dt,
            mu=mu,
            sigma=sigma,
            s0=s0,
            seed=seed_i,
        )
        p1 = plot_paths(paths, outdir)
        charts.append(os.fspath(p1))
        p2 = plot_hist(paths, outdir)
        charts.append(os.fspath(p2))
        _print({"charts": charts})
    except Exception as e:
        # One JSON line only (tests expect a single JSON blob).
        # Optionally raise when debugging.
        if bool(getattr(args, "debug", False)) or os.environ.get("COLINK_DEBUG"):
            raise
        # Emit placeholders so downstream callers see something in "charts".
        try:
            ph1 = os.path.join(outdir, "sweep_paths-PLACEHOLDER.png")
            open(ph1, "wb").close()
            charts.append(os.fspath(ph1))
        except Exception:
            pass
        try:
            ph2 = os.path.join(outdir, "sweep_hist-PLACEHOLDER.png")
            open(ph2, "wb").close()
            charts.append(os.fspath(ph2))
        except Exception:
            pass
        _print(
            {
                "error": {"type": e.__class__.__name__, "msg": str(e), "backend": backend},
                "charts": charts,
            }
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="colink-json", description="COLINK sim JSON CLI")
    parser.add_argument("--version", action="store_true", help="print version and exit")

    sub = parser.add_subparsers(dest="cmd", required=False)

    p_quote = sub.add_parser("quote", help="quote calculation → JSON")
    p_quote.add_argument("--col-in", type=float, required=True)
    p_quote.add_argument("--min-out-bps", type=float, required=True)
    p_quote.add_argument("--twap-guard", action="store_true", default=False)
    p_quote.set_defaults(func=cmd_quote)

    p_sweep = sub.add_parser("sweep", help="generate sweep charts → JSON list of files")
    p_sweep.add_argument("--outdir", type=str, default="charts")
    p_sweep.add_argument("--n-paths", type=int, default=200, dest="n_paths")
    p_sweep.add_argument("--n-steps", type=int, default=240, dest="n_steps")
    p_sweep.add_argument("--steps", type=int, dest="n_steps", help="alias for --n-steps")
    p_sweep.add_argument("--dt", type=float, default=1.0 / 240.0)
    p_sweep.add_argument("--mu", type=float, default=0.0)
    p_sweep.add_argument("--sigma", type=float, default=0.2)
    p_sweep.add_argument("--s0", type=float, default=1.0)
    p_sweep.add_argument("--seed", type=int)
    p_sweep.add_argument("--debug", action="store_true", help="raise on error")
    p_sweep.set_defaults(func=cmd_sweep)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "version", False):
        try:
            import importlib.metadata as md  # py3.8+

            print(md.version("colink-core"))
        except Exception:
            print("0.0.0")
        return 0

    if not getattr(args, "cmd", None):
        parser.print_help()
        return 2

    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
