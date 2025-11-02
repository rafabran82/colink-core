import argparse, json, re, subprocess, sys

def _num(s: str) -> float:
    return float(s.replace(",", ""))

def run(cmd):
    full = [sys.executable, "-m"] + cmd
    p = subprocess.run(full, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr.strip() or p.stdout.strip() or f"Command failed: {full}")
    return p.stdout

def quote_json(col_in, min_out_bps=None, twap_guard=False):
    cmd = ["colink_core.sim", "quote", "--col-in", str(col_in)]
    if min_out_bps is not None:
        cmd += ["--min-out-bps", str(min_out_bps)]
    if twap_guard:
        cmd += ["--twap-guard"]

    out = run(cmd)

    m1 = re.search(r"Quote:\s*([\d,\.]+)\s*COL\s*->\s*([\d,\.]+)\s*COPX\s*\|\s*eff=([\d,\.]+)", out)
    if not m1:
        raise SystemExit("Could not parse quote line:\n" + out)
    col_in_val = _num(m1.group(1))
    copx_out   = _num(m1.group(2))
    eff_rate   = _num(m1.group(3))

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

def sweep_json(outdir=None):\n    cmd = ["colink_core.sim", "sweep"]\n    if outdir:\n        cmd += ["--outdir", outdir]\n    out = run(cmd)\n    # Normalize any arrows to ASCII\n    norm = out.replace(\"\\u2192\", \"->\").replace(\"→\", \"->\")\n

    # Saved CSV / charts (supports both 'â†’' and the unicode escape)
    csv = re.search(r"Saved CSV\s*->\s*(.+)", norm)
    charts = []
    for line in norm.splitlines():\n        m = re.search(r"Saved chart\s*->\s*(.+)", line)
        if m:
            charts.append(m.group(1).strip())

    return {
        "csv": csv.group(1).strip() if csv else None,
        "charts": charts,
        "raw": out.strip()
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

