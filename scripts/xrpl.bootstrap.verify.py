import os, sys, json, datetime
def main():
    base = sys.argv[1] if len(sys.argv) > 1 else ".artifacts/data/bootstrap"
    print(f"🔎 Verifying bootstrap folder: {base}", flush=True)
    files = {
        "wallets.json": os.path.join(base, "wallets.json"),
        "trustlines.json": os.path.join(base, "trustlines.json"),
        "offers.json": os.path.join(base, "offers.json"),
        "tx_log.ndjson": os.path.join(base, "tx_log.ndjson"),
        "bootstrap_meta.json": os.path.join(base, "bootstrap_meta.json"),
        "bootstrap_plan_testnet.json": os.path.join(base, "bootstrap_plan_testnet.json"),
        "bootstrap_result_testnet.json": os.path.join(base, "bootstrap_result_testnet.json"),
        "bootstrap_summary_testnet.txt": os.path.join(base, "bootstrap_summary_testnet.txt"),
    }
    present = {k: os.path.exists(p) for k, p in files.items()}
    ndjson_lines = 0
    if present.get("tx_log.ndjson"):
        with open(files["tx_log.ndjson"], "r", encoding="utf-8") as f:
            ndjson_lines = sum(1 for _ in f if _.strip())
    ok = any(present.values())
    summary = {
        "ok": ok,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "folder": base,
        "present": present,
        "counts": {"tx_log_lines": ndjson_lines},
        "notes": ["v1 verifier: presence + tx ndjson line count only"]
    }
    print(json.dumps(summary, indent=2))
if __name__ == "__main__":
    main()
