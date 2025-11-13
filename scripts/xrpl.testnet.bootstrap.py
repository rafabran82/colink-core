"""
XRPL Testnet bootstrap for COLINK / COPX.

This script:

- Ensures issuer / user / lp wallets exist in wallets.json
- Funds them on XRPL Testnet (or Devnet) via faucet if needed
- Creates COPX trustlines (using 160-bit HEX currency code) for user + lp to issuer
- Writes a simple plan/result/meta/summary and tx_log.ndjson

Usage (from repo root):

  python scripts/xrpl.testnet.bootstrap.py ^
    --network testnet ^
    --out .artifacts/data/bootstrap ^
    --execute ^
    --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines
from xrpl.models.transactions import TrustSet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.wallet import Wallet

# 160-bit HEX currency code for COPX (ASCII "COPX" + padding)
COPX_HEX = "CPX"


# -----------------------------------
# Utility helpers
# -----------------------------------
def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2))


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def append_tx_note(txlog_path: Path, note: str, tx_hash: str | None = None) -> None:
    txlog_path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = {"ts": ts, "note": str(note)}
    if tx_hash:
        entry["hash"] = tx_hash
    with txlog_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def get_client(network: str, verbose: bool = False) -> JsonRpcClient:
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
        raise SystemExit(f"Unsupported network: {network!r} (use testnet or devnet, or set XRPL_ENDPOINT)")

    if verbose:
        print(f"[client] Using default {network} endpoint: {url}")
    return JsonRpcClient(url)


# -----------------------------------
# Faucet funding
# -----------------------------------
def account_exists(client: JsonRpcClient, addr: str) -> bool:
    req = AccountInfo(account=addr, ledger_index="validated", strict=True)
    resp = client.request(req)
    result = getattr(resp, "result", {})
    if result.get("status") == "error":
        if result.get("error") == "actNotFound":
            return False
        # Other errors: be conservative and treat as "exists" to avoid looping
        return True
    return True


def fund_wallet_if_needed(client: JsonRpcClient, network: str, label: str, addr: str, verbose: bool = False) -> None:
    if network not in {"testnet", "devnet"}:
        if verbose:
            print(f"[fund] skipping funding for {label} on non-faucet network {network}")
        return

    if account_exists(client, addr):
        if verbose:
            print(f"[fund] exists: {addr} ({label})")
        return

    faucet_base = "https://faucet.altnet.rippletest.net/accounts" if network == "testnet" else "https://faucet.devnet.rippletest.net/accounts"
    if verbose:
        print(f"[fund] requesting funds for {label}: {addr}")

    r = httpx.post(faucet_base, json={"destination": addr}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Faucet funding failed for {addr}: {r.status_code} {r.text}")

    if verbose:
        print(f"[fund] funded OK: {addr} ({label})")

    # Small delay so funding is visible to account_info
    time.sleep(2.0)


# -----------------------------------
# Trustline helpers
# -----------------------------------
def has_trustline(client: JsonRpcClient, acct: str, issuer: str, currency_hex: str = COPX_HEX) -> bool:
    req = AccountLines(account=acct)
    resp = client.request(req).result
    lines = resp.get("lines", [])
    for line in lines:
        if line.get("account") == issuer and line.get("currency") == currency_hex:
            return True
    return False


def create_trustline(
    client: JsonRpcClient,
    wallet: Wallet,
    issuer: str,
    currency_hex: str = COPX_HEX,
    limit_value: str = "1000000",
    verbose: bool = False,
) -> str:
    if has_trustline(client, wallet.classic_address, issuer, currency_hex=currency_hex):
        if verbose:
            print(f"[trustline] already exists for {wallet.classic_address}")
        return ""

    tx = TrustSet(
        account=wallet.classic_address,
        limit_amount={
            "currency": currency_hex,
            "issuer": issuer,
            "value": limit_value,
        },
    )

    if verbose:
        print(f"[trustline] creating for {wallet.classic_address}")

    tx_prepared = autofill(tx, client)
    signed = sign(tx_prepared, wallet)
    result = reliable_submission(signed, client)
    # Try to extract a hash; fall back if not present
    result_dict = getattr(result, "result", {})
    tx_json = result_dict.get("tx_json", {})
    tx_hash = tx_json.get("hash") or result_dict.get("hash") or ""
    if verbose:
        print(f"[trustline] submitted, hash={tx_hash or 'N/A'}")
    return tx_hash


# -----------------------------------
# Argparse
# -----------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--network", default="testnet", help="Network: testnet or devnet")
    p.add_argument("--out", required=True, help="Output directory for artifacts")
    p.add_argument(
        "--execute",
        action="store_true",
        help="Actually submit transactions to XRPL. If omitted, only writes plan/summary.",
    )
    p.add_argument(
        "--trustlines-only",
        action="store_true",
        help="Only perform trustline step (assumes wallets.json already exists and is funded).",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    return p.parse_args()


# -----------------------------------
# Main bootstrap flow
# -----------------------------------
def main() -> int:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    txlog_path = out_dir / "tx_log.ndjson"
    wallets_path = out_dir / "wallets.json"
    plan_path = out_dir / f"bootstrap_plan_{args.network}.json"
    result_path = out_dir / f"bootstrap_result_{args.network}.json"
    meta_path = out_dir / "bootstrap_meta.json"
    human_path = out_dir / f"bootstrap_summary_{args.network}.txt"

    # Initial plan/meta
    plan = {
        "network": args.network,
        "execute": bool(args.execute),
        "trustlines_only": bool(args.trustlines_only),
        "steps": [
            "ensure-wallets",
            "fund-wallets",
            "trustlines",
        ],
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_json(plan_path, plan)

    meta = {
        "network": args.network,
        "out_dir": str(out_dir),
        "ts_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "xrpl_endpoint": os.environ.get("XRPL_ENDPOINT", ""),
    }
    write_json(meta_path, meta)

    append_tx_note(txlog_path, "bootstrap start")

    # Load or create wallets
    wallets = read_json(wallets_path, default={})
    changed = False

    def ensure_wallet(key: str) -> dict:
        nonlocal changed, wallets
        obj = wallets.get(key)
        if obj and all(k in obj for k in ("address", "seed", "public", "private")):
            return obj
        w = Wallet.create()
        rec = {
            "address": w.classic_address,
            "seed": w.seed,
            "public": w.public_key,
            "private": w.private_key,
        }
        wallets[key] = rec
        changed = True
        append_tx_note(txlog_path, f"created {key} wallet", tx_hash=None)
        if args.verbose:
            print(f"[wallet] created {key}: {rec['address']}")
        return rec

    issuer_rec = ensure_wallet("issuer")
    user_rec = ensure_wallet("user")
    lp_rec = ensure_wallet("lp")

    if changed:
        write_json(wallets_path, wallets)

    # If we're only doing trustlines, skip funding step
    client = get_client(args.network, verbose=args.verbose)

    if not args.trustlines_only:
        # Fund wallets if needed (Testnet/Devnet)
        fund_wallet_if_needed(client, args.network, "issuer", issuer_rec["address"], verbose=args.verbose)
        fund_wallet_if_needed(client, args.network, "user", user_rec["address"], verbose=args.verbose)
        fund_wallet_if_needed(client, args.network, "lp", lp_rec["address"], verbose=args.verbose)
        append_tx_note(txlog_path, "funding finished")

    if not args.execute:
        if args.verbose:
            print("[dry-run] Not executing trustlines because --execute was not provided.")
        append_tx_note(txlog_path, "bootstrap finished (dry-run)")
        # Minimal result + summary for dry-run
        result = {
            "network": args.network,
            "execute": False,
            "trustlines_performed": False,
            "ts_end": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        write_json(result_path, result)
        human_path.write_text(
            "XRPL bootstrap (dry-run)\n"
            f"Network: {args.network}\n"
            f"Out dir: {out_dir}\n"
            "Execute: false\n"
            "Trustlines: skipped (dry-run)\n",
            encoding="utf-8",
        )
        return 0

    # Reconstruct Wallet objects from stored keys
    issuer_w = Wallet(
        seed=issuer_rec["seed"],
        public_key=issuer_rec["public"],
        private_key=issuer_rec["private"],
    )
    user_w = Wallet(
        seed=user_rec["seed"],
        public_key=user_rec["public"],
        private_key=user_rec["private"],
    )
    lp_w = Wallet(
        seed=lp_rec["seed"],
        public_key=lp_rec["public"],
        private_key=lp_rec["private"],
    )

    issuer_addr = issuer_rec["address"]

    # Trustlines: user and lp to issuer for COPX_HEX
    user_hash = create_trustline(client, user_w, issuer_addr, currency_hex=COPX_HEX, verbose=args.verbose)
    append_tx_note(txlog_path, "trustline created (user -> issuer COPX_HEX)", tx_hash=user_hash or None)

    lp_hash = create_trustline(client, lp_w, issuer_addr, currency_hex=COPX_HEX, verbose=args.verbose)
    append_tx_note(txlog_path, "trustline created (lp -> issuer COPX_HEX)", tx_hash=lp_hash or None)

    write_json(out_dir / "trustlines.json", {"currency_hex": COPX_HEX, "accounts": ["user", "lp"]})

    # Final result + human summary
    result = {
        "network": args.network,
        "execute": True,
        "trustlines_performed": True,
        "user_trustline_hash": user_hash,
        "lp_trustline_hash": lp_hash,
        "ts_end": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_json(result_path, result)

    summary_lines = [
        "XRPL bootstrap result",
        f"Network: {args.network}",
        f"Out dir: {out_dir}",
        "",
        f"Issuer: {issuer_rec['address']}",
        f"User:   {user_rec['address']}",
        f"LP:     {lp_rec['address']}",
        "",
        f"COPX_HEX: {COPX_HEX}",
        "",
        f"User trustline tx: {user_hash or 'N/A'}",
        f"LP trustline tx:   {lp_hash or 'N/A'}",
    ]
    human_path.write_text("\n".join(summary_lines), encoding="utf-8")

    append_tx_note(txlog_path, "bootstrap finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())



