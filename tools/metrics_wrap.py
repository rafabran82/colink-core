#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / ".artifacts"


def try_get(d, keys):
    for k in keys:
        cur = d
        ok = True
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur
    return None


def coerce_number(x):
    if isinstance(x, int | float):
        return float(x)
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    try:
        return float(str(x))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", default=str(ART))
    args = ap.parse_args()

    base = pathlib.Path(args.artifacts)
    if not base.exists():
        print(f"No artifacts dir: {base}", file=sys.stderr)
        return 2

    jsons = sorted(base.rglob("*.json"))
    if not jsons:
        print("No JSONs to wrap.")
        return 0

    produced = 0
    for p in jsons:
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print(f"[SKIP] {p}: invalid JSON: {e}")
            continue

        # Already wrapped?
        if isinstance(data, dict) and isinstance(data.get("metrics"), dict):
            continue

        now_iso = dt.datetime.now(dt.UTC).isoformat()
        run_id = p.stem
        backend = try_get(data, ["backend", "display", "renderer"])
        osname = try_get(data, ["os", "system"])
        sha = try_get(data, ["sha", "git_sha", "commit"])
        ts = try_get(data, ["timestamp", "time"]) or now_iso

        sr = coerce_number(
            try_get(data, ["success_rate", "successRate", "summary.success_rate", "ok"])
        )
        p95 = coerce_number(
            try_get(
                data,
                [
                    "p95_latency_ms",
                    "p95",
                    "latency.p95_ms",
                    "summary.p95_latency_ms",
                    "latency_p95_ms",
                    "metrics.p95_ms",
                ],
            )
        )
        orders = coerce_number(try_get(data, ["orders_total", "orders", "summary.orders"]))
        trades = coerce_number(try_get(data, ["trades_total", "trades", "summary.trades"]))
        vol_q = coerce_number(try_get(data, ["volume_quote", "volume", "summary.volume_quote"]))
        pnl = coerce_number(try_get(data, ["pnl", "summary.pnl"]))

        metrics_doc = {
            "run_id": run_id,
            "timestamp": ts,
            "backend": backend,
            "os": osname,
            "sha": sha,
            "schema_version": 1,
            "metrics": {
                "success_rate": sr,
                "p95_latency_ms": p95,
                "orders_total": orders,
                "trades_total": trades,
                "volume_quote": vol_q,
                "pnl": pnl,
            },
        }

        out = p.with_name(f"{p.stem}.metrics.json")
        out.write_text(json.dumps(metrics_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        produced += 1
        print(f"[OK] Wrapped -> {out}")

    print(f"Produced {produced} metrics JSON file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
