#!/usr/bin/env python3
import argparse, json, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = ROOT / ".artifacts"

def read_ndjson_count(dirpath: pathlib.Path) -> int:
    # Count first *.ndjson in same dir (if any)
    for nd in sorted(dirpath.glob("*.ndjson")):
        try:
            with nd.open("r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            pass
    return 0

def coalesce(*vals):
    for v in vals:
        if v not in (None, "", []):
            return v
    return None

def is_metrics_json(p: pathlib.Path):
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        return isinstance(data, dict) and isinstance(data.get("metrics"), dict)
    except Exception:
        return False

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

    metrics_files = [p for p in artifacts.rglob("*.json") if is_metrics_json(p)]
    if not metrics_files:
        print("No metrics JSONs found to collect.", file=sys.stderr)
        sys.exit(3)

    rows = []
    for mfile in sorted(metrics_files):
        data = json.loads(mfile.read_text(encoding="utf-8-sig"))
        nd_count = read_ndjson_count(mfile.parent)

        run_id   = coalesce(data.get("run_id"), mfile.stem)
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
