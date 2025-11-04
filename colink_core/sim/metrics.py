from __future__ import annotations
import argparse, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Simple chart SLO gates")
    ap.add_argument("--dir", default="artifacts/charts", help="Charts directory")
    ap.add_argument("--min-files", type=int, default=2, help="Minimum number of PNG charts")
    ap.add_argument("--min-total-kb", type=int, default=20, help="Minimum total PNG size (KB)")
    args = ap.parse_args()

    d = Path(args.dir)
    pngs = sorted(d.glob("*.png"))
    total_kb = sum(p.stat().st_size for p in pngs) / 1024.0

    print(f"[metrics] charts_dir={d} png_count={len(pngs)} total_kb={total_kb:.1f}")

    ok = True
    if len(pngs) < args.min_files:
        print(f"[metrics][FAIL] need at least {args.min_files} PNGs, got {len(pngs)}")
        ok = False
    if total_kb < args.min_total_kb:
        print(f"[metrics][FAIL] need at least {args.min_total_kb} KB total, got {total_kb:.1f} KB")
        ok = False

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
