#!/usr/bin/env python3
import json
import time
import os
from pathlib import Path

import httpx
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo
from xrpl.models.transactions import TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.wallet import Wallet

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

COL_CODE = "COL"
COPX_HEX = "4350580000000000000000000000000000000000"  # "CPX" padded

DEFAULT_OUT = Path(".artifacts/data/bootstrap")

# ------------------------------------------------------------
# CLIENT
# ------------------------------------------------------------

def get_client(network: str, verbose=False) -> JsonRpcClient:
    override = os.environ.get("XRPL_ENDPOINT")
    if override:
        if verbose:
            print(f"[client] Using XRPL_ENDPOINT={override}")
        return JsonRpcClient(override)

    if network == "testnet":
        url = "https://s.altnet.rippletest.net:51234"
    elif network == "devnet":
        url = "https://s.devnet.rippletest.net:51234"
    else:
        raise SystemExit(f"Unsupported network: {network}")

    if verbose:
        print(f"[client] Using default {network} endpoint: {url}")
    return JsonRpcClient(url)

# ------------------------------------------------------------
# ACCOUNT HELPERS
# ------------------------------------------------------------

def account_exists(client: JsonRpcClient, addr: str) -> bool:
    req = AccountInfo(account=addr, ledger_index="validated", strict=True)
    try:
        resp = client.request(req)
        result = getattr(resp, "result", {})
        if result.get("status") == "error":
            if result.get("error") == "actNotFound":
                return False
            return True
        return True
    except Exception:
        return False

def wait_for_activation(client: JsonRpcClient, addr: str, verbose=False):
    for i in range(30):
        if account_exists(client, addr):
            if verbose:
                print(f"[activation] OK: {addr}")
            return
        if verbose:
            print(f"[activation] waiting {addr}...")
        time.sleep(2)
    raise SystemExit(f"Account {addr} did not activate in time")

# ------------------------------------------------------------
# FAUCET FUNDING
# ------------------------------------------------------------

def fund(client: JsonRpcClient, network: str, label: str, addr: str, verbose=False):
    if account_exists(client, addr):
        if verbose:
            print(f"[fund] already active: {addr} ({label})")
        return

    faucet_url = (
        "https://faucet.altnet.rippletest.net/accounts"
        if network == "testnet"
        else "https://faucet.devnet.rippletest.net/accounts"
    )

    if verbose:
        print(f"[fund] requesting faucet for {label}: {addr}")

    r = httpx.post(faucet_url, json={"destination": addr}, timeout=20)
    if r.status_code != 200:
        raise SystemExit(f"Faucet failed for {addr}: {r.status_code} {r.text}")

    wait_for_activation(client, addr, verbose=verbose)

# ------------------------------------------------------------
# TRUSTLINES
# ------------------------------------------------------------

def create_trustline(client, wallet: Wallet, issuer: Wallet, currency: str, verbose=False):
    if verbose:
        print(f"[trustline] {wallet.classic_address} → {currency}")

    tx = TrustSet(
        account=wallet.classic_address,
        limit_amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer.classic_address,
            value="1000000000"
        )
    )
    prepared = autofill(tx, client)
    signed = sign(prepared, wallet)
    resp = submit_and_wait(signed, client)
    if verbose:
        print(f"[trustline] result: {resp.result}")

# ------------------------------------------------------------
# TOKENS
# ------------------------------------------------------------

def issue_token(client, issuer: Wallet, dest: Wallet, currency: str, amount: str, verbose=False):
    if verbose:
        print(f"[issue] {amount} {currency} → {dest.classic_address}")

    tx = Payment(
        account=issuer.classic_address,
        destination=dest.classic_address,
        amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer.classic_address,
            value=amount
        )
    )
    prepared = autofill(tx, client)
    signed = sign(prepared, issuer)
    resp = submit_and_wait(signed, client)
    if verbose:
        print("[issue] result:", resp.result)

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--network", default="testnet")
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--execute", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    verbose = args.verbose
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    # Create wallets
    issuer = Wallet.create()
    user = Wallet.create()
    lp = Wallet.create()

    if verbose:
        print("[wallets]")
        print(" issuer:", issuer.classic_address)
        print(" user  :", user.classic_address)
        print(" lp    :", lp.classic_address)

    client = get_client(args.network, verbose=verbose)

    if args.execute:
        fund(client, args.network, "issuer", issuer.classic_address, verbose)
        fund(client, args.network, "user", user.classic_address, verbose)
        fund(client, args.network, "lp", lp.classic_address, verbose)

        create_trustline(client, user, issuer, COL_CODE, verbose)
        create_trustline(client, lp, issuer, COL_CODE, verbose)
        create_trustline(client, user, issuer, COPX_HEX, verbose)
        create_trustline(client, lp, issuer, COPX_HEX, verbose)

        issue_token(client, issuer, user, COL_CODE, "1000000", verbose)
        issue_token(client, issuer, lp, COL_CODE, "1000000", verbose)
        issue_token(client, issuer, user, COPX_HEX, "1000000", verbose)
        issue_token(client, issuer, lp, COPX_HEX, "1000000", verbose)

    # Save JSON
    data = {
        "issuer": issuer.seed,
        "user": user.seed,
        "lp": lp.seed,
        "addresses": {
            "issuer": issuer.classic_address,
            "user": user.classic_address,
            "lp": lp.classic_address,
        }
    }
    (outdir / "bootstrap.json").write_text(json.dumps(data, indent=2))

    print("[done] bootstrap complete")
    return 0

if __name__ == "__main__":
    main()
