#!/usr/bin/env python3
import argparse, json, pathlib, sys, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / ".artifacts"

def try_get(d, keys):
    # search for any key (dot-paths allowed like "stats.p95")
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
    if isinstance(x, (int, float)):
        return float(x)
    # convert bool to number
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    # string numbers
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
        # Skip already-conforming metrics JSON
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print(f"[SKIP] {p}: invalid JSON: {e}")
            continue

        if isinstance(data, dict) and isinstance(data.get("metrics"), dict):
            # Already metrics-style, nothing to do
            continue

        # Derive basic fields
        now_iso = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()
        run_id = p.stem
        backend = try_get(data, ["backend", "display", "renderer"])
        osname  = try_get(data, ["os", "system"])
        sha     = try_get(data, ["sha", "git_sha", "commit"])
        ts      = try_get(data, ["timestamp", "time"]) or now_iso

        # Try to map common summary fields
        sr = try_get(data, ["success_rate", "successRate", "summary.success_rate", "ok"])
        sr = coerce_number(sr)

        p95 = try_get(data, [
            "p95_latency_ms", "p95", "latency.p95_ms", "summary.p95_latency_ms",
            "latency_p95_ms", "metrics.p95_ms"
        ])
        p95 = coerce_number(p95)

        orders = coerce_number(try_get(data, ["orders_total", "orders", "summary.orders"]))
        trades = coerce_number(try_get(data, ["trades_total", "trades", "summary.trades"]))
        vol_q  = coerce_number(try_get(data, ["volume_quote", "volume", "summary.volume_quote"]))
        pnl    = coerce_number(try_get(data, ["pnl", "summary.pnl"]))

        metrics_doc = {
            "run_id": run_id,
            "timestamp": ts,
            "backend": backend,
            "os": osname,
            "sha": sha,
            "metrics": {
                "success_rate": sr,            # may be None; schema will allow null
                "p95_latency_ms": p95,         # may be None; schema will allow null
                "orders_total": orders,
                "trades_total": trades,
                "volume_quote": vol_q,
                "pnl": pnl
            }
        }

        out = p.with_name(f"{p.stem}.metrics.json")
        out.write_text(json.dumps(metrics_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        produced += 1
        print(f"[OK] Wrapped → {out}")

    print(f"Produced {produced} metrics JSON file(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
