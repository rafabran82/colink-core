from __future__ import annotations
import argparse, json, pathlib, platform, datetime as dt
from .sim import Pool, BridgeRoute, BridgeSim

def _mk_route(pairA: str, pairM: str, fee1_bps: float, fee2_bps: float) -> BridgeRoute:
    # pairA:  A/M  ; pairM:  M/B
    a, m = pairA.split("/")
    m2, b = pairM.split("/")
    if m != m2:
        raise ValueError(f"middle asset mismatch: {pairA} vs {pairM}")
    # Asymmetric reserves to create realistic slippage
    p1 = Pool(base=a, quote=m, x=1_000_000.0, y=950_000.0, fee_bps=fee1_bps)
    p2 = Pool(base=m, quote=b, x=900_000.0,  y=1_050_000.0, fee_bps=fee2_bps)
    return BridgeRoute(hop1=p1, hop2=p2, a=a, m=m, b=b)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=777)
    ap.add_argument("--amount", type=float, default=1_000.0, help="amount in A")
    ap.add_argument("--pairA", type=str, default="COL/COPX", help="first hop pair A/M")
    ap.add_argument("--pairM", type=str, default="COPX/XRP", help="second hop pair M/B")
    ap.add_argument("--fee1_bps", type=float, default=30.0)
    ap.add_argument("--fee2_bps", type=float, default=30.0)
    ap.add_argument("--out-prefix", type=str, default="./.artifacts/bridge_demo")
    ap.add_argument("--backend", type=str, default="Agg")
    ap.add_argument("--sha", type=str, default="")
    args = ap.parse_args()

    route = _mk_route(args.pairA, args.pairM, args.fee1_bps, args.fee2_bps)
    sim = BridgeSim(seed=args.seed)
    res = sim.simulate(route, amount_in=args.amount)

    prefix = pathlib.Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    stem = prefix  # keep provided name as stem

    # events NDJSON: single record for now
    ev_path = stem.with_suffix(".events.ndjson")
    ev_path.write_text(json.dumps({"type": "route_result", **res}) + "\n", encoding="utf-8")

    # metrics JSON (collector-friendly *.metrics.json)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    metrics = {
        "run_id": stem.name,
        "timestamp": ts,
        "backend": args.backend,
        "os": platform.platform(),
        "sha": args.sha,
        "schema_version": "colink.bridge.v1",
        "route": res["route"],
        "pairs": {"hop1": args.pairA, "hop2": args.pairM},
        "metrics": {
            "success_rate": 1.0 if res["success"] else 0.0,
            "p95_latency_ms": res["p95_latency_ms"],
            "fees_total": res["fees_total"],
            "slippage_bps": res["slippage_bps"],
            "effective_price_ab": res["effective_price_ab"],
            "ideal_price_ab": res["ideal_price_ab"],
            "amount_in": res["amount_in"],
            "amount_out": res["amount_out"],
        },
    }
    m_path = stem.with_suffix(".metrics.json")
    m_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "out_events": str(ev_path), "out_metrics": str(m_path)}))

if __name__ == "__main__":
    main()
