from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Chart + slip SLO gates")
    ap.add_argument("--dir", default="artifacts/charts", help="Charts directory (recursive)")
    ap.add_argument("--min-files", type=int, default=2, help="Min number of PNG charts")
    ap.add_argument("--min-total-kb", type=int, default=20, help="Min total PNG size (KB)")
    ap.add_argument("--summary", default="artifacts/summary.json", help="Optional summary.json")
    ap.add_argument(
        "--max-slip-bps", type=float, default=None, help="Fail if max_slip_bps exceeds this"
    )
    args = ap.parse_args()

    d = Path(args.dir)
    pngs = sorted(d.rglob("*.png"))
    total_kb = sum(p.stat().st_size for p in pngs) / 1024.0

    print(f"[metrics] charts_root={d} png_count={len(pngs)} total_kb={total_kb:.1f}")
    for p in pngs[:10]:
        print(f" - {p} ({p.stat().st_size / 1024.0:.1f} KB)")

    ok = True
    if len(pngs) < args.min_files:
        print(f"[metrics][FAIL] need >= {args.min_files} PNGs, got {len(pngs)}")
        ok = False
    if total_kb < args.min_total_kb:
        print(f"[metrics][FAIL] need >= {args.min_total_kb} KB total, got {total_kb:.1f} KB")
        ok = False

    # Optional slip SLO
    if args.max_slip_bps is not None:
        sp = Path(args.summary)
        if sp.exists():
            data = json.loads(sp.read_text(encoding="utf-8-sig"))
            mx = float(data.get("max_slip_bps", 0.0))
            print(f"[metrics] summary.max_slip_bps={mx} (limit {args.max_slip_bps})")
            if mx > float(args.max_slip_bps):
                print(f"[metrics][FAIL] max_slip_bps {mx} > {args.max_slip_bps}")
                ok = False
        else:
            print(f"[metrics][WARN] summary file not found: {sp} (skip slip SLO)")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

