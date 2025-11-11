import argparse, csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ts, avg = [], []
    with open(args.csv, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                ts.append(datetime.fromisoformat(row["timestamp_utc"]))
                avg.append(float(row["total_mb_avg"]))
            except Exception:
                # skip bad rows
                pass

    if not ts:
        print("[WARN] no data to plot")
        return

    plt.figure(figsize=(6,3))
    plt.plot(ts, avg, marker="o")
    plt.title("Sim Runs — Avg Total MB")
    plt.xlabel("Run (UTC)")
    plt.ylabel("Avg Total MB")

    # basic label readability
    for lbl in plt.gca().get_xticklabels():
        lbl.set_rotation(20)
        lbl.set_ha("right")

    plt.tight_layout()
    plt.savefig(args.out, dpi=150)
    print("[OK] Wrote", args.out)

if __name__ == "__main__":
    main()
