import argparse
import json
import re
import subprocess
import sys

def run(args):
    """
    Run `python -m <args>` and return stdout as text.
    """
    cmd = [sys.executable, "-m"] + list(args)
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out.decode("utf-8", errors="replace")

def _num(s):
    return float(s.replace(",", ""))

def quote_json(col_in, min_out_bps=None, twap_guard=False):
    cmd = ["colink_core.sim", "quote", "--col-in", str(col_in)]
    if min_out_bps is not None:
        cmd += ["--min-out-bps", str(min_out_bps)]
    if twap_guard:
        cmd += ["--twap-guard"]

    out = run(cmd)

    # Example lines:
    # Quote: 8,000.000000 COL -> 920,685.291906 COPX  | eff=115.085661 COPX/COL
    #   Min-out @150.0 bps: 906,875.012527 COPX
    #   TWAP guard: dev=793.1 bps  budget=1043.1 bps  => OK

    m = re.search(
        r"Quote:\s*([\d,\.]+)\s*COL\s*[-\u2192>]+\s*([\d,\.]+)\s*COPX\s*\|\s*eff=([\d,\.]+)",
        out
    )
    if not m:
        raise SystemExit("Could not parse quote output:\n" + out)

    col_in_val = _num(m.group(1))
    copx_out   = _num(m.group(2))
    eff_rate   = _num(m.group(3))

    min_bps = None
    min_out = None
    m2 = re.search(r"Min-out\s*@([\d\.]+)\s*bps:\s*([\d,\.]+)", out)
    if m2:
        min_bps = float(m2.group(1))
        min_out = _num(m2.group(2))

    twap = None
    m3 = re.search(r"TWAP guard:\s*dev=([\d,\.]+)\s*bps\s*budget=([\d,\.]+)\s*bps\s*=>\s*(\w+)", out)
    if m3:
        twap = {
            "dev_bps": _num(m3.group(1)),
            "budget_bps": _num(m3.group(2)),
            "ok": (m3.group(3).upper() == "OK")
        }

    return {
        "col_in": col_in_val,
        "copx_out": copx_out,
        "eff_copx_per_col": eff_rate,
        "min_out_bps": min_bps,
        "min_out": min_out,
        "twap_guard": twap,
        "raw": out.strip()
    }

def sweep_json(outdir=None):
    cmd = ["colink_core.sim", "sweep"]
    if outdir:
        cmd += ["--outdir", outdir]
    out = run(cmd)

    # Normalize arrows to ASCII so parsing is stable across consoles
    norm = out.replace("\u2192", "->").replace("â†’", "->")

    csv_m = re.search(r"Saved CSV\s*->\s*(.+)", norm)
    charts = []
    for line in norm.splitlines():
        m = re.search(r"Saved chart\s*->\s*(.+)", line)
        if m:
            charts.append(m.group(1).strip())

    return {
        "csv": csv_m.group(1).strip() if csv_m else None,
        "charts": charts,
        "raw": norm.strip()
    }

def main():
    ap = argparse.ArgumentParser(description="JSON wrapper for colink_core.sim CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quote", help="Emit JSON for a single quote")
    q.add_argument("--col-in", type=float, required=True)
    q.add_argument("--min-out-bps", type=float, default=None)
    q.add_argument("--twap-guard", action="store_true")

    s = sub.add_parser("sweep", help="Run sweep and emit JSON with artifact paths")
    s.add_argument("--outdir", default=None)

    args = ap.parse_args()

    if args.cmd == "quote":
        data = quote_json(args.col_in, args.min_out_bps, args.twap_guard)
    else:
        data = sweep_json(args.outdir)

    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")

if __name__ == "__main__":
    main()
