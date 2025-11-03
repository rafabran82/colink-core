import sys, os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import ServerState

load_dotenv(".env.testnet")
RPC = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")

def read_json_utf8_any(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    path = sys.argv[1] if len(sys.argv)>1 else None
    if not path or not os.path.exists(path):
        print(json.dumps({"ok": False, "messages": ["missing file"], "file": path}))
        return
    rec = read_json_utf8_any(path)

    msgs = []
    qty   = Decimal(rec.get("qty_copx","0"))
    px    = Decimal(rec.get("price_xrp","0"))
    cap   = int(rec.get("cap_drops",0))

    step1 = rec.get("step1") or {}
    step2 = rec.get("step2") or {}
    er1   = step1.get("engine_result")
    er2   = step2.get("engine_result")
    h1    = step1.get("hash")
    h2    = step2.get("hash")
    fee1  = int(step1.get("fee_drops", 0) or 0)
    fee2  = int(step2.get("fee_drops", 0) or 0)

    if er1 != "tesSUCCESS": msgs.append(f"Step1 engine_result != tesSUCCESS: {er1}")
    if er2 != "tesSUCCESS": msgs.append(f"Step2 engine_result != tesSUCCESS: {er2}")
    if not h1: msgs.append("Step1 hash missing")
    if not h2: msgs.append("Step2 hash missing")

    # Expectation:
    # - maker receives ~cap drops (subject to path caps; here step1 sends cap directly)
    # - taker spends cap + fee1 drops (fee2 is paid by issuer in step2)
    expected_taker_delta = -(cap + fee1)

    # When you want to pull live balances to check deltas, you can extend here.
    # For now, just sanity-check fee and cap presence.
    if cap <= 0:
        msgs.append("cap_drops <= 0")
    if fee1 < 0:
        msgs.append("step1 fee invalid")

    ok = len(msgs)==0
    print(json.dumps({
        "file": os.path.basename(path),
        "ok": ok,
        "messages": msgs,
        "summary": {
            "qty_copx": str(qty),
            "price_xrp": str(px),
            "cap_drops": cap,
            "step1_engine": er1,
            "step1_hash": h1,
            "step1_fee_drops": fee1,
            "step2_engine": er2,
            "step2_hash": h2,
            "step2_fee_drops": fee2,
            "expected_taker_delta_drops": expected_taker_delta
        }
    }, indent=2))
if __name__ == "__main__":
    main()
