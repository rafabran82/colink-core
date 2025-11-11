import argparse, json, math, random, statistics, time
from datetime import datetime, timezone
from pathlib import Path

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--n", type=int, default=60, help="Number of samples")
    ap.add_argument("--dt", type=float, default=0.05, help="Seconds between samples")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # --- Generate tiny synthetic timeline ---
    values = []
    ndjson_path = out / "events.ndjson"
    with ndjson_path.open("w", encoding="utf-8") as f:
        base = random.uniform(10, 20)
        for i in range(args.n):
            # gentle trend + sine + noise (pretend “MB processed”)
            val = base + 0.05*i + 2.0*math.sin(i/7.0) + random.uniform(-0.3, 0.3)
            values.append(val)
            evt = {
                "ts": iso_now(),
                "seq": i,
                "metric": "total_mb",
                "value": round(val, 3)
            }
            f.write(json.dumps(evt) + "\n")
            time.sleep(args.dt)

    # --- Metrics summary ---
    p95 = statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values)
    metrics = {
        "generated_at": iso_now(),
        "samples": len(values),
        "total_mb_min": round(min(values), 3),
        "total_mb_avg": round(statistics.fmean(values), 3),
        "total_mb_p95": round(p95, 3),
        "total_mb_max": round(max(values), 3),
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # light breadcrumb for other tools
    (out / "_ok").write_text("ok", encoding="utf-8")

if __name__ == "__main__":
    main()
