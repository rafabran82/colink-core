import json, sys, pathlib

def read_json(p):
    # Accept UTF-8 with or without BOM
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        try:
            return int(float(x))
        except Exception:
            return default

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "messages": ["No file arg"]}))
        return

    path = sys.argv[1]
    try:
        obj = read_json(path)
    except Exception as e:
        print(json.dumps({"ok": False, "messages": [f"Read/JSON error: {e!r}"], "file": pathlib.Path(path).name}))
        return

    schema = obj.get("schema") or ("1.0" if "params" in obj and "results" in obj else ("legacy" if "timestamp" in obj else "unknown"))

    # Extract fields (schema 1.0 vs legacy)
    if schema == "1.0":
        params   = obj.get("params", {}) or {}
        qty_copx  = params.get("qty_copx")
        price_xrp = params.get("price_xrp")
        slippage  = params.get("slippage")
        cap_drops = to_int(params.get("cap_drops"))
        step1     = obj.get("step1", {}) or {}
        step2     = obj.get("step2", {}) or {}
        results   = obj.get("results", {}) or {}
        ts_iso    = obj.get("ts_iso")
    else:
        qty_copx  = obj.get("qty_copx")
        price_xrp = obj.get("price_xrp")
        slippage  = obj.get("slippage")
        cap_drops = to_int(obj.get("cap_drops"))
        step1     = obj.get("step1", {}) or {}
        step2     = obj.get("step2", {}) or {}
        results   = {
            "maker_delta_drops": None,
            "taker_delta_drops": None,
            "est_gross_drops": None
        }
        ts_iso    = obj.get("timestamp")

    s1_eng = step1.get("engine_result")
    s1_h   = step1.get("hash")
    s1_fee = to_int(step1.get("fee_drops"))
    s2_eng = step2.get("engine_result")
    s2_h   = step2.get("hash")
    s2_fee = to_int(step2.get("fee_drops"))

    maker_dx = results.get("maker_delta_drops")
    taker_dx = results.get("taker_delta_drops")
    est_gross= results.get("est_gross_drops")

    maker_dx = None if maker_dx is None else to_int(maker_dx)
    taker_dx = None if taker_dx is None else to_int(taker_dx)
    est_gross= None if est_gross is None else to_int(est_gross)

    msgs, ok = [], True

    if not cap_drops or cap_drops <= 0:
        ok = False; msgs.append("cap_drops <= 0")

    if s1_eng != "tesSUCCESS": ok = False; msgs.append(f"Step1 engine_result != tesSUCCESS: {s1_eng}")
    if s2_eng != "tesSUCCESS": ok = False; msgs.append(f"Step2 engine_result != tesSUCCESS: {s2_eng}")
    if not s1_h: ok = False; msgs.append("Step1 hash missing")
    if not s2_h: ok = False; msgs.append("Step2 hash missing")

    # Soft sanity checks
    soft = []
    if cap_drops and maker_dx is not None:
        allowed_maker = {cap_drops, cap_drops - 10, cap_drops + 10}
        if maker_dx not in allowed_maker:
            soft.append(f"maker_delta_drops {maker_dx} not in {sorted(allowed_maker)}")
    if cap_drops and taker_dx is not None:
        allowed_taker = {-cap_drops, -(cap_drops - 10), -(cap_drops + 10)}
        if taker_dx not in allowed_taker:
            soft.append(f"taker_delta_drops {taker_dx} not in {sorted(allowed_taker)}")

    out = {
        "file": pathlib.Path(path).name,
        "ok": ok,
        "messages": msgs + (["SOFT: " + m for m in soft] if soft else []),
        "summary": {
            "schema": schema,
            "ts_iso": ts_iso,
            "qty_copx": str(qty_copx) if qty_copx is not None else None,
            "price_xrp": str(price_xrp) if price_xrp is not None else None,
            "slippage": str(slippage) if slippage is not None else None,
            "cap_drops": cap_drops,
            "step1_engine": s1_eng, "step1_hash": s1_h, "step1_fee_drops": s1_fee,
            "step2_engine": s2_eng, "step2_hash": s2_h, "step2_fee_drops": s2_fee,
            "maker_delta_drops": maker_dx,
            "taker_delta_drops": taker_dx,
            "est_gross_drops": est_gross,
        }
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
