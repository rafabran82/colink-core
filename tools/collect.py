import argparse, json, sys, csv, pathlib
from datetime import datetime
import pandas as pd

def _sanitize_for_parquet(df: 'pd.DataFrame') -> 'pd.DataFrame':
    import numpy as np
    # 1) Coerce known numeric columns to floats (or Int64 where appropriate)
    numeric_cols = [
        'events_count','success_rate','p95_latency_ms',
        'orders_total','trades_total','volume_quote','pnl',
        'slippage_bps','amount_out'
    ]
    for col in [c for c in numeric_cols if c in df.columns]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2) Decode any bytes in object columns and unify dtype
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: x.decode('utf-8','ignore') if isinstance(x, (bytes, bytearray)) else x)
        # Keep them as pandas 'string' dtype for Arrow friendliness
        df[col] = df[col].astype('string')

    # 3) Optional: stable column order (nice for diffs)
    preferred = ['kind','run_id','timestamp','backend','os','sha','events_count',
                 'success_rate','p95_latency_ms','orders_total','trades_total',
                 'volume_quote','pnl','slippage_bps','amount_out']
    ordered = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    return df[ordered]


def classify_kind(obj):
    sv = obj.get("schema_version")
    if sv == "colink.bridge.v1":
        return "bridge"
    return "sim"

def as_str(x):
    return "" if x is None else str(x)

def collect(artifacts: pathlib.Path, out_csv: pathlib.Path, out_parquet: pathlib.Path,
            os_val: str | None, sha_val: str | None, backend: str | None):
    rows = []
    for p in artifacts.glob("*.metrics.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        kind = classify_kind(obj)
        run_id = obj.get("run_id", p.stem.replace(".metrics",""))
        ts = obj.get("timestamp") or obj.get("generated_at") or datetime.utcnow().isoformat()+"Z"
        metrics = obj.get("metrics", {}) or {}

        base = {
            "kind": kind,
            "run_id": run_id,
            "timestamp": ts,
            "backend": backend or obj.get("backend") or "",
            "os": os_val or obj.get("os") or "",
            "sha": sha_val or obj.get("sha") or "",
            "events_count": obj.get("events_count", ""),
            "success_rate": metrics.get("success_rate", ""),
            "p95_latency_ms": metrics.get("p95_latency_ms", ""),
            "orders_total": metrics.get("orders_total", ""),
            "trades_total": metrics.get("trades_total", ""),
            "volume_quote": metrics.get("volume_quote", ""),
            "pnl": metrics.get("pnl", ""),
        }

        # Bridge extras (if present)
        if kind == "bridge":
            base["slippage_bps"] = metrics.get("slippage_bps", "")
            base["amount_in"]    = metrics.get("amount_in", "")
            base["amount_out"]   = metrics.get("amount_out", "")
        else:
            base["slippage_bps"] = ""
            base["amount_in"]    = ""
            base["amount_out"]   = ""

        rows.append(base)

    if not rows:
        print("No metrics files found to collect.")
        return

    df = pd.DataFrame(rows)
    df.sort_values(["timestamp","kind","run_id"], inplace=True, ignore_index=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
df = _sanitize_for_parquet(df)\n    df.to_parquet(out_parquet, index=False)
    print(f"Wrote {len(df)} rows → {out_csv}")
    print(f"Wrote Parquet → {out_parquet}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", required=True)
    ap.add_argument("--out-dataset", required=True)
    ap.add_argument("--out-parquet", required=True)
    ap.add_argument("--os", dest="os_val")
    ap.add_argument("--sha", dest="sha_val")
    ap.add_argument("--backend")
    args = ap.parse_args()

    collect(
        artifacts=pathlib.Path(args.artifacts),
        out_csv=pathlib.Path(args.out_dataset),
        out_parquet=pathlib.Path(args.out_parquet),
        os_val=args.os_val,
        sha_val=args.sha_val,
        backend=args.backend
    )

if __name__ == "__main__":
    main()

