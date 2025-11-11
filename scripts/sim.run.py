import argparse, json, math, random, statistics, time
from datetime import datetime, timezone
from pathlib import Path

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def gen_latency_ms(i: int) -> float:
    """
    Small synthetic latency model:
      - base ~ 150–180 ms
      - gentle wave
      - rare spikes
    """
    base = 165.0 + 8.0*math.sin(i/9.0)
    noise = random.uniform(-4.0, 4.0)
    # 3% chance of a small spike
    spike = 0.0
    if random.random() < 0.03:
        spike = random.uniform(25.0, 60.0)
    return max(0.0, base + noise + spike)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--n", type=int, default=60, help="Number of samples")
    ap.add_argument("--dt", type=float, default=0.05, help="Seconds between samples")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # --- Generate tiny synthetic timeline ---
    mb_values = []
    lat_values = []
    ndjson_path = out / "events.ndjson"
    with ndjson_path.open("w", encoding="utf-8") as f:
        base = random.uniform(10, 20)
        for i in range(args.n):
            # pretend “MB processed”
            mb = base + 0.05*i + 2.0*math.sin(i/7.0) + random.uniform(-0.3, 0.3)
            mb_values.append(mb)

            # synthetic latency
            lat = gen_latency_ms(i)
            lat_values.append(lat)

            evt = {
                "ts": iso_now(),
                "seq": i,
                "metrics": {
                    "total_mb": round(mb, 3),
                    "latency_ms": round(lat, 1)
                }
            }
            f.write(json.dumps(evt) + "\n")
            time.sleep(args.dt)

    # --- Metrics summary ---
    def p95(vs):
        # statistics.quantiles requires enough samples; guard for short runs
        if len(vs) >= 20:
            return statistics.quantiles(vs, n=20)[18]
        return max(vs) if vs else 0.0

    metrics = {
        "generated_at": iso_now(),
        "samples": len(mb_values),
        "total_mb_min": round(min(mb_values), 3),
        "total_mb_avg": round(statistics.fmean(mb_values), 3),
        "total_mb_p95": round(p95(mb_values), 3),
        "total_mb_max": round(max(mb_values), 3),

        # NEW latency rollups
        "latency_ms_p50": round(statistics.median(lat_values), 1),
        "latency_ms_p95": round(p95(lat_values), 1),
        "latency_ms_max": round(max(lat_values), 1),
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (out / "_ok").write_text("ok", encoding="utf-8")

if __name__ == "__main__":
    main()
import json, random, time, pathlib

def write_metrics(out_dir: str):
    """Generate and save simple metrics.json for CI aggregation."""
    out = pathlib.Path(out_dir)
    m = {
        "success_rate": round(random.uniform(0.9, 1.0), 3),
        "avg_latency_ms": round(random.uniform(50, 200), 2),
        "tx_count": random.randint(50, 500),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(out / "metrics.json", "w") as f:
        json.dump(m, f, indent=2)
    print(f"✅ Metrics written: {out / 'metrics.json'}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Simulate a run (placeholder)
    print(f"Running COLINK simulation to {args.out}")
    time.sleep(1.0)
    write_metrics(args.out)
