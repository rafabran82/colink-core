#!/usr/bin/env python3
"""
XRPL Testnet Bootstrap - Simple Stable Edition (Phase 4 MVP)
- Creates issuer, user, lp wallets
- Funds them via Testnet faucet
- Creates COPX trustlines
- Outputs artifacts into --out directory
"""

import sys
import json
import time
import argparse
import httpx
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import TrustSet
from xrpl.wallet import Wallet
from xrpl.transaction import sign, autofill, send_reliable_submission
from xrpl.models.requests import AccountInfo, AccountLines

# -----------------------------------
# Utility: read/write JSON with no BS
# -----------------------------------
def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2))


# --------------------------
# Faucet funding for Testnet
# --------------------------
def fund_wallet(addr: str):
    faucet = "https://faucet.altnet.rippletest.net/accounts"
    print(f"[fund] requesting funds for: {addr}")

    r = httpx.post(faucet, json={"destination": addr}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Faucet error: {r.text}")

    print(f"[fund] funded OK: {addr}")


# --------------------------
# Trustline check helper
# --------------------------
def has_trustline(client, acct, issuer, currency="434F505800000000000000000000000000000000"):
    req = AccountLines(account=acct)
    resp = client.request(req).result
    if "lines" not in resp:
        return False
    for line in resp["lines"]:
        if line.get("currency") == currency and line.get("account") == issuer:
            return True
    return False


# --------------------------
# Create trustline for wallet
# --------------------------
def create_trustline(client, wallet: Wallet, issuer: str):
    tx = TrustSet(
        account=wallet.classic_address,
        limit_amount={
            "currency": "434F505800000000000000000000000000000000",
            "issuer": issuer,
            "value": "1000000",
        },
    )

    print(f"[trustline] creating for {wallet.classic_address}")

    tx_prepared = autofill(tx, client)
    signed = sign(tx_prepared, wallet)
    result = send_reliable_submission(signed, client)

    print(f"[trustline] OK: {result}")


# --------------------------
# Main bootstrap flow
# --------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--network", required=True, help="testnet or devnet")
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # connect client
    url = "https://s.altnet.rippletest.net:51234"
    client = JsonRpcClient(url)

    # Load or create wallets.json
    wallets_path = out_dir / "wallets.json"
    if wallets_path.exists():
        wallets = json.loads(wallets_path.read_text())
    else:
        wallets = {"issuer": None, "user": None, "lp": None}

    # Create wallets if missing
    changed = False
    for label in ["issuer", "user", "lp"]:
        if wallets[label] is None:
            w = Wallet.create()
            wallets[label] = {
                "address": w.classic_address,
                "seed": w.seed,
                "public": w.public_key,
                "private": w.private_key,
            }
            changed = True
            print(f"[wallet] created {label}: {w.classic_address}")

    if changed:
        write_json(wallets_path, wallets)

    # Real wallet objects reconstructed
    issuer_w = Wallet(
        seed=wallets["issuer"]["seed"],
        public_key=wallets["issuer"]["public"],
        private_key=wallets["issuer"]["private"],
    )
    user_w = Wallet(
        seed=wallets["user"]["seed"],
        public_key=wallets["user"]["public"],
        private_key=wallets["user"]["private"],
    )
    lp_w = Wallet(
        seed=wallets["lp"]["seed"],
        public_key=wallets["lp"]["public"],
        private_key=wallets["lp"]["private"],
    )

    # -----------------------------
    # FUNDING (testnet faucet)
    # -----------------------------
    if args.execute:
        for w in [issuer_w, user_w, lp_w]:
            try:
                # check if exists
                info = client.request(AccountInfo(account=w.classic_address))
                if "account_data" in info.result:
                    print(f"[fund] exists: {w.classic_address}")
                    continue
            except Exception:
                pass

            # faucet fund
            fund_wallet(w.classic_address)
            time.sleep(3)

    # -----------------------------
    # TRUSTLINES
    # -----------------------------
    trust_path = out_dir / "trustlines.json"
    trustlines = []

    if args.execute:
        issuer_addr = issuer_w.classic_address

        # user trustline
        if not has_trustline(client, user_w.classic_address, issuer_addr):
            create_trustline(client, user_w, issuer_addr)
            trustlines.append("user")

        # lp trustline
        if not has_trustline(client, lp_w.classic_address, issuer_addr):
            create_trustline(client, lp_w, issuer_addr)
            trustlines.append("lp")

        write_json(trust_path, trustlines)

    print("[bootstrap] finished OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())


