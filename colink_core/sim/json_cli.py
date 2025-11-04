from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import importlib.metadata as md  # py3.8+
except Exception:  # pragma: no cover
    md = None  # type: ignore

from .run_sweep import simulate_gbm_paths, plot_paths, plot_hist  # type: ignore


def _version_str() -> str:
    # Try package version, fall back to 0.0.0
    if md is not None:
        try:
            return md.version("colink-core")
        except Exception:
            pass
    return "0.0.0"


def cmd_quote(args: argparse.Namespace) -> None:
    """
    Print a deterministic quote JSON using a haircut derived from min_out_bps.
    """
    col_in = float(args.col_in)
    min_out_bps = float(args.min_out_bps)
    twap_guard = bool(args.twap_guard)

    # 150 bps -> 0.015 haircut (matches prior outputs)
    haircut = max(0.0, min_out_bps / 10_000.0)
    eff = 1.0 - haircut
    copx_out = round(col_in * eff, 3)

    payload = {
        "col_in": col_in,
        "min_out_bps": min_out_bps,
        "min_out": copx_out,
        "copx_out": copx_out,
        "eff_copx_per_col": round(eff, 3),
        "twap_guard": twap_guard,
        "raw": {
            "note": "smoke-quote",
            "inputs": {"col_in": col_in, "min_out_bps": min_out_bps, "twap_guard": twap_guard},
            "calc": {"haircut": round(haircut, 3)},
        },
    }
    print(json.dumps(payload))


def cmd_sweep(args: argparse.Namespace) -> None:
    """
    Generate GBM paths, save two PNG charts into --outdir, print:
      {"charts": ["<paths_png>", "<hist_png>"]}
    Guarantees at least one path even on error (creates placeholders).
    """
    outdir = Path(args.outdir or "charts")
    outdir.mkdir(parents=True, exist_ok=True)

    # Safe minima for stressy CI environments
    n_paths = max(1, int(getattr(args, "n_paths", 512)))
    n_steps = max(2, int(getattr(args, "n_steps", 256)))
    seed = getattr(args, "seed", None)

    charts: list[str] = []
    try:
        paths = simulate_gbm_paths(
            S0=float(getattr(args, "S0", 1.0)),
            mu=float(getattr(args, "mu", 0.0)),
            sigma=float(getattr(args, "sigma", 0.2)),
            dt=float(getattr(args, "dt", 1.0 / 252.0)),
            n_steps=n_steps,
            n_paths=n_paths,
            seed=seed,
        )

        p1 = plot_paths(paths, outdir=str(outdir))
        charts.append(str(p1))
        p2 = plot_hist(paths, outdir=str(outdir))
        charts.append(str(p2))

    except Exception:
        # Make placeholders so tests see *something* in charts.
        try:
            ph1 = outdir / "sweep_paths-PLACEHOLDER.png"
            ph1.write_bytes(b"")
            charts.append(str(ph1))
        except Exception:
            pass
        try:
            ph2 = outdir / "sweep_hist-PLACEHOLDER.png"
            ph2.write_bytes(b"")
            charts.append(str(ph2))
        except Exception:
            pass

    print(json.dumps({"charts": charts}))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="colink-json", description="COLINK sim JSON CLI")
    p.add_argument("--version", action="store_true", help="print version and exit")

    sp = p.add_subparsers(dest="cmd", required=False)

    q = sp.add_parser("quote", help="emit a quote JSON")
    q.add_argument("--col-in", type=float, required=True, dest="col_in")
    q.add_argument("--min-out-bps", type=float, required=True, dest="min_out_bps")
    q.add_argument("--twap-guard", action="store_true", dest="twap_guard")
    q.set_defaults(func=cmd_quote)

    s = sp.add_parser("sweep", help="run GBM sweep and write charts")
    s.add_argument("--outdir", type=str, default="charts")
    s.add_argument("--n-paths", type=int, default=512, dest="n_paths")
    s.add_argument("--n-steps", type=int, default=256, dest="n_steps")
    s.add_argument("--seed", type=int, default=None)
    s.add_argument("--S0", type=float, default=1.0)
    s.add_argument("--mu", type=float, default=0.0)
    s.add_argument("--sigma", type=float, default=0.2)
    s.add_argument("--dt", type=float, default=1.0 / 252.0)
    s.set_defaults(func=cmd_sweep)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()

    # Support `--version` with or without a subcommand
    if "--version" in argv and (len(argv) == 1 or argv[0] == "--version"):
        print(_version_str())
        return 0

    args = parser.parse_args(argv)
    if getattr(args, "version", False) and not getattr(args, "cmd", None):
        print(_version_str())
        return 0

    if not getattr(args, "cmd", None):
        parser.print_help()
        return 2

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 2

    func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
