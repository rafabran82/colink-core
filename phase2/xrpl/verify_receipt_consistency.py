import json, sys, os
from decimal import Decimal

def main():
    if len(sys.argv) < 2:
        print("Usage: verify_receipt_consistency.py <receipt.json>")
        sys.exit(2)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        rec = json.load(f)

    qty    = Decimal(str(rec["params"]["qty_copx"]))
    price  = Decimal(str(rec["params"]["price_xrp"]))
    cap    = int(rec["params"]["cap_drops"])

    maker_before = int(rec["before"]["maker"]["xrp_drops"])
    maker_after  = int(rec["after"]["maker"]["xrp_drops"])
    taker_before = int(rec["before"]["taker"]["xrp_drops"])
    taker_after  = int(rec["after"]["taker"]["xrp_drops"])

    maker_delta = maker_after - maker_before
    taker_delta = taker_after - taker_before

    est_gross_drops = int((qty * price * Decimal(1_000_000)).to_integral_value())

    # Expectation envelope:
    # - taker should decrease by approx est_gross_drops (<= cap); maker increases by similar
    # - issuer sends COPX (checked indirectly by step2 engine_result)
    s1 = rec["step1"].get("engine_result")
    s2 = rec["step2"].get("engine_result")

    ok = True
    msgs = []

    if s1 != "tesSUCCESS":
        ok = False
        msgs.append(f"Step1 engine_result != tesSUCCESS: {s1}")
    if s2 != "tesSUCCESS":
        ok = False
        msgs.append(f"Step2 engine_result != tesSUCCESS: {s2}")

    if not (-cap <= taker_delta <= 0):
        ok = False
        msgs.append(f"Taker delta drops {taker_delta} not in [-cap, 0] with cap={cap}")

    if not (0 <= maker_delta <= cap):
        ok = False
        msgs.append(f"Maker delta drops {maker_delta} not in [0, cap] with cap={cap}")

    # At minimum, maker_delta should be close to -taker_delta (fees are negligible on testnet)
    if maker_delta + taker_delta != 0:
        # allow tiny off-by-one if ever happens; on testnet usually exact 0
        if abs(maker_delta + taker_delta) > 10:
            ok = False
            msgs.append(f"Maker+Taker deltas not balancing to ~0: maker {maker_delta}, taker {taker_delta}")

    # est_gross_drops is informational; we don't hard-fail if price*qty != exact ledger match
    out = {
        "file": os.path.basename(path),
        "ok": ok,
        "messages": msgs,
        "summary": {
            "qty_copx": str(qty),
            "price_xrp": str(price),
            "cap_drops": cap,
            "est_gross_drops": est_gross_drops,
            "maker_delta_drops": maker_delta,
            "taker_delta_drops": taker_delta,
            "step1_engine": s1,
            "step1_hash": rec["step1"].get("hash"),
            "step2_engine": s2,
            "step2_hash": rec["step2"].get("hash")
        }
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
