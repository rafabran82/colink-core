#!/usr/bin/env python3
import argparse, json, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = ROOT / ".artifacts"

def read_ndjson_count(p: pathlib.Path) -> int:
    try:
        with p.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0

def coalesce(*vals):
    for v in vals:
        if v not in (None, "", []):
            return v
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", default=str(DEFAULT_ARTIFACTS))
    ap.add_argument("--out-dataset", required=True)
    ap.add_argument("--out-parquet", required=False)
    ap.add_argument("--backend", default=None, help="Override backend column")
    ap.add_argument("--os", dest="osname", default=None, help="Override OS column")
    ap.add_argument("--sha", default=None, help="Override SHA column")
    args = ap.parse_args()

    artifacts = pathlib.Path(args.artifacts)
    if not artifacts.exists():
        print(f"No artifacts dir: {artifacts}", file=sys.stderr)
        sys.exit(2)

    rows = []
    metrics_files = sorted(artifacts.rglob("*.metrics.json"))

    for mfile in metrics_files:
        data = json.loads(mfile.read_text(encoding="utf-8"))

        stem = mfile.name[:-len(".metrics.json")]
        ndjson = list(mfile.parent.glob(f"{stem}.events.ndjson"))
        nd_count = read_ndjson_count(ndjson[0]) if ndjson else 0

        run_id   = coalesce(data.get("run_id"), stem)
        backend  = coalesce(args.backend, data.get("backend"))
        osname   = coalesce(args.osname, data.get("os"))
        sha      = coalesce(args.sha, data.get("sha"))
        ts       = coalesce(data.get("timestamp"), "")

        metrics  = data.get("metrics", {})
        row = {
            "run_id": run_id,
            "timestamp": ts,
            "backend": backend,
            "os": osname,
            "sha": sha,
            "events_count": nd_count,
            "success_rate": metrics.get("success_rate"),
            "p95_latency_ms": metrics.get("p95_latency_ms"),
            "orders_total": metrics.get("orders_total"),
            "trades_total": metrics.get("trades_total"),
            "volume_quote": metrics.get("volume_quote"),
            "pnl": metrics.get("pnl"),
        }
        rows.append(row)

    if not rows:
        print("No metrics files found to collect.", file=sys.stderr)
        sys.exit(3)

    df = pd.DataFrame(rows)
    key_cols = ["run_id", "timestamp", "backend", "os", "sha", "events_count"]
    metric_cols = [c for c in df.columns if c not in key_cols]
    df = df[key_cols + metric_cols]

    out_csv = pathlib.Path(args.out_dataset)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    if args.out_parquet:
        out_parq = pathlib.Path(args.out_parquet)
        df.to_parquet(out_parq, index=False)

    print(f"Wrote {len(df)} rows → {out_csv}")
    if args.out_parquet:
        print(f"Wrote Parquet → {args.out_parquet}")

if __name__ == "__main__":
    sys.exit(main())
