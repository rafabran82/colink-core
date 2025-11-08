import argparse
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


def _read_metrics(files: List[Path]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p in files:
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            # Skip unreadable JSONs
            continue

        # Common fields
        row: Dict[str, Any] = {
            "run_id": obj.get("run_id"),
            "timestamp": obj.get("timestamp"),
            "backend": obj.get("backend"),
            "os": obj.get("os"),
            "sha": obj.get("sha"),
            "schema_version": obj.get("schema_version"),
        }

        # Kind tagging (sim vs bridge) if we can infer it
        sv = str(obj.get("schema_version", "")).lower()
        if "bridge" in sv:
            row["kind"] = "bridge"
            m = obj.get("metrics", {}) or {}
            row["events_count"] = m.get("events_count")
            row["slippage_bps"] = m.get("slippage_bps")
            row["amount_out"] = m.get("amount_out")
        else:
            row["kind"] = "sim"
            m = obj.get("metrics", {}) or {}
            row["events_count"] = m.get("events_count")
            row["success_rate"] = m.get("success_rate")
            row["p95_latency_ms"] = m.get("p95_latency_ms")
            row["orders_total"] = m.get("orders_total")
            row["trades_total"] = m.get("trades_total")
            row["volume_quote"] = m.get("volume_quote")
            row["pnl"] = m.get("pnl")

        rows.append(row)

    return rows


def _sanitize_for_parquet(df: "pd.DataFrame") -> "pd.DataFrame":
    # 1) Coerce known numeric columns to numeric (floats/ints). Non-parsable → NaN
    numeric_cols = [
        "events_count", "success_rate", "p95_latency_ms",
        "orders_total", "trades_total", "volume_quote", "pnl",
        "slippage_bps", "amount_out",
    ]
    for col in [c for c in numeric_cols if c in df.columns]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2) Decode bytes in object columns and make them pandas 'string' dtype
    obj_cols = list(df.select_dtypes(include=["object"]).columns)
    if obj_cols:
        def _decode(x):
            if isinstance(x, (bytes, bytearray)):
                try:
                    return x.decode("utf-8", "ignore")
                except Exception:
                    return str(x)
            return x
        for col in obj_cols:
            df[col] = df[col].map(_decode)
            df[col] = df[col].astype("string")

    # 3) Nice column order
    preferred = [
        "kind", "run_id", "timestamp", "backend", "os", "sha", "schema_version",
        "events_count", "success_rate", "p95_latency_ms",
        "orders_total", "trades_total", "volume_quote", "pnl",
        "slippage_bps", "amount_out",
    ]
    ordered = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    return df[ordered]


def collect(artifacts_dir: Path, out_dataset: Path, out_parquet: Path, os_name: str | None, sha: str | None, backend: str | None) -> None:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    # Pick up only *.metrics.json produced by wrappers
    files = sorted(artifacts_dir.glob("*.metrics.json"))
    rows = _read_metrics(files)
    df = pd.DataFrame(rows)

    # Allow CLI overrides (ensure columns exist first)
    if "os" not in df.columns:
        df["os"] = None
    if "sha" not in df.columns:
        df["sha"] = None
    if "backend" not in df.columns:
        df["backend"] = None
    if os_name:
        df.loc[:, "os"] = os_name
    if sha:
        df.loc[:, "sha"] = sha
    if backend:
        df.loc[:, "backend"] = backend

    df = _sanitize_for_parquet(df)

    out_dataset.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dataset, index=False)
    df.to_parquet(out_parquet, index=False)
    print(f"Wrote {len(df)} rows → {out_dataset}")
    print(f"Wrote Parquet → {out_parquet}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", required=True, help="Directory containing *.metrics.json")
    ap.add_argument("--out-dataset", required=True, help="CSV output path")
    ap.add_argument("--out-parquet", required=True, help="Parquet output path")
    ap.add_argument("--os", dest="os_name", default=None)
    ap.add_argument("--sha", default=None)
    ap.add_argument("--backend", default=None)
    args = ap.parse_args()

    collect(
        artifacts_dir=Path(args.artifacts),
        out_dataset=Path(args.out_dataset),
        out_parquet=Path(args.out_parquet),
        os_name=args.os_name,
        sha=args.sha,
        backend=args.backend,
    )


if __name__ == "__main__":
    main()
