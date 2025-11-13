#!/usr/bin/env python3
import argparse
import json
import logging
import sys
import time
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo
from xrpl.wallet import Wallet

from xrpl_compat import safe_sign_and_autofill_transaction, send_reliable_submission

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--network", default="testnet", help="Network: testnet or devnet")
    p.add_argument("--out", required=True, help="Directory to write bootstrap artifacts")
    p.add_argument("--execute", action="store_true", help="Actually submit transactions")
    p.add_argument("--trustlines-only", action="store_true", help="Only trustline step")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    return p.parse_args()

def _write_json(path_obj: Path, obj):
    path_obj.write_text(json.dumps(obj, indent=2))

def _append_tx_note(txlog_path: Path, note: str):
    txlog_path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = {"ts": ts, "note": note}
    with txlog_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

def main():
    args = parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    endpoint = "https://s.altnet.rippletest.net:51234"
    client = JsonRpcClient(endpoint)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    txlog_path = out_dir / "tx_log.ndjson"
    if not txlog_path.exists():
        _append_tx_note(txlog_path, "bootstrap started")

    wallets_path = out_dir / "wallets.json"
    if wallets_path.exists():
        wallets = json.loads(wallets_path.read_text())
    else:
        wallets = {"issuer": None, "user": None, "lp": None}

    # --- Create wallets ---
    if wallets["issuer"] is None:
        w = Wallet.create()
        wallets["issuer"] = {
            "address": w.classic_address,
            "seed": w.seed,
            "public": w.public_key,
            "private": w.private_key,
        }
        _append_tx_note(txlog_path, "created issuer wallet")

    if wallets["user"] is None:
        w = Wallet.create()
        wallets["user"] = {
            "address": w.classic_address,
            "seed": w.seed,
            "public": w.public_key,
            "private": w.private_key,
        }
        _append_tx_note(txlog_path, "created user wallet")

    if wallets["lp"] is None:
        w = Wallet.create()
        wallets["lp"] = {
            "address": w.classic_address,
            "seed": w.seed,
            "public": w.public_key,
            "private": w.private_key,
        }
        _append_tx_note(txlog_path, "created LP wallet")

    _write_json(wallets_path, wallets)

    # If only creating wallets, exit here.
    if args.trustlines_only:
        _append_tx_note(txlog_path, "trustlines-only mode ended")
        return 0

    # --- Trustlines ---
    if args.execute:
        from xrpl.models.transactions import TrustSet

        issuer = wallets["issuer"]["address"]
        limit_value = "1000000"


# --- # --- FUNDING MODULE START ---

import time
import httpx

def fund_if_needed(label, w):
    print(f"[fund] checking {label} ({w['address']})")
    faucet_url = "https://faucet.altnet.rippletest.net/accounts"

    # Check if account already exists
    try:
        from xrpl.models.requests import AccountInfo
        req = AccountInfo(account=w["address"], ledger_index="current", strict=True)
        resp = client.request(req)
        if resp.is_successful():
            print(f"[fund] {label} already exists on-ledger")
            return
    except Exception:
        pass

    print(f"[fund] requesting faucet for {label}...")
    r = httpx.post(faucet_url, json={"destination": w["address"]})
    if r.status_code != 200:
        print(f"[fund] faucet ERROR for {label}: {r.text}")
        return

    print(f"[fund] faucet OK → waiting 5 seconds...")
    time.sleep(5)

# --- # --- FUNDING MODULE END ---
def ensure_trustline(wallet_record, label):
    w = Wallet(seed=wallet_record["seed"], public_key=wallet_record["public"], private_key=wallet_record["private"])
    tx = TrustSet(
                account=w.classic_address,
                limit_amount={
                    "currency": "COPX",
                    "issuer": issuer,
                    "value": limit_value,
                },
            )
    signed = safe_sign_and_autofill_transaction(tx, w, client)
    send_reliable_submission(signed, client)
    _append_tx_note(txlog_path, f"created trustline for {label}")

    ensure_trustline(wallets["user"], "user")
    ensure_trustline(wallets["lp"], "lp")

    _write_json(out_dir / "trustlines.json", ["user", "lp"])
        _append_tx_note(txlog_path, "trustlines finished")

    _append_tx_note(txlog_path, "bootstrap finished")
    return 0

if __name__ == "__main__":
    sys.exit(main())





