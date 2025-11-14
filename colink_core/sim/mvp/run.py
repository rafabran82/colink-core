from __future__ import annotations
import json, os, sys, time, random, argparse
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="XRP/COL", help="Trading pair symbol")
    ap.add_argument("--steps", type=int, default=60, help="Number of ticks")
    ap.add_argument("--seed", type=int, default=42, help="PRNG seed")
    ap.add_argument("--out", default="./.artifacts", help="Artifacts folder")
    args = ap.parse_args()

    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    # Emit events.ndjson (one per tick)
    ev_path = os.path.join(args.out, "sim.events.ndjson")
    with open(ev_path, "w", encoding="utf-8") as f:
        price = 1.0000
        depth = 10_000.0
        for t in range(args.steps):
            # simple random walk + depth wobble
            price *= (1.0 + random.uniform(-0.001, 0.001))
            depth += random.uniform(-150, 150)
            evt = {
                "ts": now_iso(),
                "t": t,
                "pair": args.pair,
                "mid_price": round(price, 6),
                "pool_depth": max(0.0, round(depth, 2)),
                "spread_bps": round(random.uniform(2, 8), 3),
                "slippage_bps": round(random.uniform(0, 15), 3),
            }
            f.write(json.dumps(evt) + "\n")
            time.sleep(0.0, ensure_ascii=False, indent=2)  # keep instant for MVP

    # Summarize simple metrics
    met_path = os.path.join(args.out, "sim.metrics.json")
    metrics = {
        "schema_version": "mvp-0.1",
        "pair": args.pair,
        "steps": args.steps,
        "seed": args.seed,
        "started_at": now_iso(),
        "completed_at": now_iso(),
        "notes": "MVP random-walk liquidity sim",
    }
    with open(met_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Drop a CSV summary (compatible with your index)
    csv_path = os.path.join(args.out, "sim.summary.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("key,value\n")
        for k, v in metrics.items():
            if isinstance(v, (str, int, float)):
                f.write(f"{k},{v}\n")

    print("Sim complete:")
    print(" ", ev_path)
    print(" ", met_path)
    print(" ", csv_path)

if __name__ == "__main__":
    sys.exit(main())
