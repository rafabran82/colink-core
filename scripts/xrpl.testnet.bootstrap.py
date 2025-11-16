from __future__ import annotations
# ============================================================
# Wait until XRPL account exists on ledger
# ============================================================
def wait_for_activation(client, address, retries=20, sleep_s=1):
    import time
    from xrpl.asyncio.account import get_account_root
    import asyncio

    for i in range(retries):
        try:
            root = asyncio.run(get_account_root(address, client))
            if "Sequence" in root:
                print(f"[wait] {address} is ACTIVE")
                return True
        except Exception:
            pass
        print(f"[wait] {address} not active yet... ({i+1}/{retries})")
        time.sleep(sleep_s)
    raise Exception(f"Account {address} did not activate in time.")

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

# ============================================================
# Wait until XRPL account exists on ledger
# ============================================================
def wait_for_activation(client, address, retries=20, sleep_s=1):
    import time
    from xrpl.asyncio.account import get_account_root
    import asyncio

    for i in range(retries):
        try:
            root = asyncio.run(get_account_root(address, client))
            if "Sequence" in root:
                print(f"[wait] {address} is ACTIVE")
                return True
        except Exception:
            pass
        print(f"[wait] {address} not active yet... ({i+1}/{retries})")
        time.sleep(sleep_s)
    raise Exception(f"Account {address} did not activate in time.")

import argparse
import json
import os
import sys
import time

def wait_for_activation(client, address, timeout=20, sleep_s=1):
    """Polls for account activation before proceeding."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            info = client.request({
                "method": "account_info",
                "params": [{"account": address}]
            }).result
            if "account_data" in info:
                print(f"[fund] activation confirmed: {address}")
                return
        except Exception:
            pass
        time.sleep(sleep_s)
    raise Exception(f"Account {address} did not activate in time.")
# ============================================================
# Wait until XRPL account exists on ledger
# ============================================================
def wait_for_activation(client, address, retries=20, sleep_s=1):
    import time
    from xrpl.asyncio.account import get_account_root
    import asyncio

    for i in range(retries):
        try:
            root = asyncio.run(get_account_root(address, client))
            if "Sequence" in root:
                print(f"[wait] {address} is ACTIVE")
                return True
        except Exception:
            pass
        print(f"[wait] {address} not active yet... ({i+1}/{retries})")
        time.sleep(sleep_s)
    raise Exception(f"Account {address} did not activate in time.")

# ============================================================
# Wait until XRPL account exists on ledger
# ============================================================
def wait_for_activation(client, address, retries=20, sleep_s=1):
    import time
    from xrpl.asyncio.account import get_account_root
    import asyncio

    for i in range(retries):
        try:
            root = asyncio.run(get_account_root(address, client))
            if "Sequence" in root:
                print(f"[wait] {address} is ACTIVE")
                return True
        except Exception:
            pass
        print(f"[wait] {address} not active yet... ({i+1}/{retries})")
        time.sleep(sleep_s)
    raise Exception(f"Account {address} did not activate in time.")

import time
from decimal import Decimal
from pathlib import Path

import httpx
import time

def wait_for_activation(client, address, max_tries=30, sleep_s=2):
    """
    Wait until an XRPL account is activated (has an AccountRoot).
    """
    for i in range(max_tries):
        try:
            acct = client.request({
                "command": "account_info",
                "account": address,
                "ledger_index": "validated"
            })
            if acct and not ("error" in acct.result):
                print(f"[activation] OK: {address}")
                return
        except Exception:
            pass
        print(f"[activation] waiting for {address} (try {i+1}/{max_tries}) ...")
        time.sleep(sleep_s)
    raise Exception(f"Account {address} did not activate in time.")
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers
from xrpl.models.transactions import TrustSet, Payment, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.wallet import Wallet

# 160-bit HEX currency code for COPX (ASCII "COPX" + padding)
COPX_HEX = "CPX"

# --- COL token + COPX<->COL pool config ------------------------------

# Human-readable COL token code (standard 3â€“4 char issuer token)
COL_CODE = "COL"

# Initial COL distribution (issued by issuer to LP + user)
COL_LP_ISSUE_AMOUNT = "500000"   # 500k COL for liquidity provider
COL_USER_ISSUE_AMOUNT = "10000"   # small COL balance for user testing

# LP pool seeding for the COPX<->COL DEX offers
# Idea: 1 COL ~ 10 COPX (arbitrary test rate for simulations)
COPX_LP_SELL_AMOUNT = "100000"    # LP sells 100k COPX for COL
COL_LP_BUY_AMOUNT   = "10000"     # ... wants 10k COL in return

COL_LP_SELL_AMOUNT  = "10000"     # LP sells 10k COL for COPX
COPX_LP_BUY_AMOUNT  = "100000"    # ... wants 100k COPX in return


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
        fh.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n")


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
    # --- Faucet funding ---
    if network not in ["testnet", "devnet"]:
        if verbose:
            print(f"[fund] skipping funding for {label} on non-faucet network {network}")
        return

    if account_exists(client, addr):
        if verbose:
            print(f"[fund] already activated: {addr} ({label})")
        return

    if verbose:
        print(f"[fund] requesting faucet for {label}: {addr}")

    faucet_base = (
        "https://faucet.altnet.rippletest.net/accounts"
        if network == "testnet"
        else "https://faucet.devnet.rippletest.net/accounts"
    )

    r = httpx.post(faucet_base, json={"destination": addr}, timeout=20)

    if r.status_code != 200:
        raise RuntimeError(
            f"Faucet funding failed for {addr}: {r.status_code} {r.text}"
        )

    # Wait for activation
    wait_for_activation(client, addr)
    time.sleep(2.0)


# -----------------------------------
# COL issuance helpers
def issue_col_to_wallet(
    client: JsonRpcClient,
    issuer_wallet: Wallet,
    dest_wallet: Wallet,
    amount: str,
    verbose: bool = False,
) -> str:
    """
    Send COL_CODE issued by issuer_wallet to dest_wallet.

    Creates an IOU Payment from the issuer to the destination using
    IssuedCurrencyAmount. Assumes the destination already has a COL trustline.
    """
    tx = Payment(
        account=issuer_wallet.classic_address,
        destination=dest_wallet.classic_address,
        amount=IssuedCurrencyAmount(
            currency=COL_CODE,
            issuer=issuer_wallet.classic_address,
            value=amount,
        ),
    )
    if verbose:
        print(f"[col-issue] {amount} {COL_CODE} -> {dest_wallet.classic_address}")

    tx_prepared = autofill(tx, client)
    signed = sign(tx_prepared, issuer_wallet)
    try:
        result = submit_and_wait(signed, client)
    except Exception as e:
        if verbose:
            print(f"[col-issue] ERROR during COL issue: {e}")
        return ""

    tx_result = (getattr(result, "result", None) or result)
    tx_hash = None
    if isinstance(tx_result, dict):
        tx_hash = (tx_result.get("tx_json") or {}).get("hash") or tx_result.get("hash")

    if verbose:
        print(f"[col-issue] submitted, hash={tx_hash or "N/A"}")

    return tx_hash or ""


def issue_copx_to_wallet(
    client: JsonRpcClient,
    issuer_wallet: Wallet,
    dest_wallet: Wallet,
    amount: str,
    verbose: bool = False,
) -> str:
    """
    Send COPX (COPX_HEX) issued by issuer_wallet to dest_wallet.

    Assumes the destination already has a COPX trustline to the issuer.
    """
    tx = Payment(
        account=issuer_wallet.classic_address,
        destination=dest_wallet.classic_address,
        amount=IssuedCurrencyAmount(
            currency=COPX_HEX,
            issuer=issuer_wallet.classic_address,
            value=amount,
        ),
    )
    if verbose:
        print(f"[copx-issue] {amount} COPX -> {dest_wallet.classic_address}")

    tx_prepared = autofill(tx, client)
    signed = sign(tx_prepared, issuer_wallet)
    try:
        result = submit_and_wait(signed, client)
    except Exception as e:
        if verbose:
            print(f"[copx-issue] ERROR during COPX issue: {e}")
        return ""

    tx_result = (getattr(result, "result", None) or result)
    tx_hash = None
    if isinstance(tx_result, dict):
        tx_hash = (tx_result.get("tx_json") or {}).get("hash") or tx_result.get("hash")

    if verbose:
        print(f"[copx-issue] submitted, hash={tx_hash}")

    return tx_hash or ""

def create_copx_col_offer(
    client: JsonRpcClient,
    lp_wallet: Wallet,
    taker_gets: IssuedCurrencyAmount,
    taker_pays: IssuedCurrencyAmount,
    verbose: bool = False,
) -> str:
    """
    Generic helper to create a COPX<->COL IOU offer from the LP wallet.

    taker_gets: the amount the LP is offering to sell.
    taker_pays: the amount the LP wants in return.
    """
    tx = OfferCreate(
        account=lp_wallet.classic_address,
        taker_gets=taker_gets,
        taker_pays=taker_pays,
    )
    if verbose:
        print(f"[dex-offer] submitting offer from {lp_wallet.classic_address}")

    tx_prepared = autofill(tx, client)
    signed = sign(tx_prepared, lp_wallet)
    try:
        result = submit_and_wait(signed, client)
    except Exception as e:
        if verbose:
            print(f"[col-issue] ERROR during COL issue: {e}")
        return ""

    tx_result = (getattr(result, "result", None) or result)
    tx_hash = None
    if isinstance(tx_result, dict):
        tx_hash = (tx_result.get("tx_json") or {}).get("hash") or tx_result.get("hash")

    if verbose:
        print(f"[dex-offer] submitted, hash={tx_hash}")

    return tx_hash or ""

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
    try:
        result = submit_and_wait(signed, client)
    except Exception as e:
        if verbose:
            print(f"[col-issue] ERROR during COL issue: {e}")
        return ""
    # Try to extract a hash; fall back if not present
    result_dict = getattr(result, "result", {})
    tx_json = result_dict.get("tx_json", {})
    tx_hash = tx_json.get("hash") or result_dict.get("hash") or ""
    if verbose:
        print(f"[trustline] submitted, hash={tx_hash or 'N/A'}")
    return tx_hash


# COL trustline helper (thin wrapper around create_trustline)
def create_col_trustline(
    client: JsonRpcClient,
    wallet: Wallet,
    issuer: str,
    limit_value: str = "1000000",
    verbose: bool = False,
) -> str:
    """
    Create (or ensure) a COL trustline from the given wallet to the issuer.

    This uses the existing generic create_trustline helper but passes COL_CODE
    as the currency. Keeping this as a thin wrapper makes it easier to evolve
    COL-specific behavior later without touching the COPX path.
    """
    return create_trustline(
        client=client,
        wallet=wallet,
        issuer=issuer,
        currency_hex=COL_CODE,
        limit_value=limit_value,
        verbose=verbose,
    )


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
    user_hash = create_trustline(
        client,
        user_w,
        issuer_addr,
        currency_hex=COPX_HEX,
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        "trustline created (user -> issuer COPX_HEX)",
        tx_hash=user_hash or None,
    )

    lp_hash = create_trustline(
        client,
        lp_w,
        issuer_addr,
        currency_hex=COPX_HEX,
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        "trustline created (lp -> issuer COPX_HEX)",
        tx_hash=lp_hash or None,
    )

    # Additional COL trustlines: user and lp to issuer for COL_CODE
    col_user_hash = create_col_trustline(
        client=client,
        wallet=user_w,
        issuer=issuer_addr,
        limit_value="1000000",
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        "trustline created (user -> issuer COL_CODE)",
        tx_hash=col_user_hash or None,
    )

    col_lp_hash = create_col_trustline(
        client=client,
        wallet=lp_w,
        issuer=issuer_addr,
        limit_value="1000000",
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        "trustline created (lp -> issuer COL_CODE)",
        tx_hash=col_lp_hash or None,
    )

    # COL issuance: issuer -> user and lp
    col_user_issue_hash = issue_col_to_wallet(
        client=client,
        issuer_wallet=issuer_w,
        dest_wallet=user_w,
        amount=COL_USER_ISSUE_AMOUNT,
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        f"COL issued to user ({COL_USER_ISSUE_AMOUNT})",
        tx_hash=col_user_issue_hash or None,
    )

    col_lp_issue_hash = issue_col_to_wallet(
        client=client,
        issuer_wallet=issuer_w,
        dest_wallet=lp_w,
        amount=COL_LP_ISSUE_AMOUNT,
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        f"COL issued to lp ({COL_LP_ISSUE_AMOUNT})",
        tx_hash=col_lp_issue_hash or None,
    )

    # COPX issuance: issuer -> lp (for second side of pool)
    copx_lp_issue_hash = issue_copx_to_wallet(
        client=client,
        issuer_wallet=issuer_w,
        dest_wallet=lp_w,
        amount="100000",
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        "COPX issued to lp (100000)",
        tx_hash=copx_lp_issue_hash or None,
    )

    # Seed COPX<->COL DEX: LP sells COL for COPX at ~10:1
    dex_col_sells_hash = create_copx_col_offer(
        client=client,
        lp_wallet=lp_w,
        taker_gets=IssuedCurrencyAmount(
            currency=COL_CODE,
            issuer=issuer_addr,
            value=COL_LP_SELL_AMOUNT,
        ),
        taker_pays=IssuedCurrencyAmount(
            currency=COPX_HEX,
            issuer=issuer_addr,
            value=COPX_LP_BUY_AMOUNT,
        ),
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        f"DEX offer created (LP sells {COL_LP_SELL_AMOUNT} COL for {COPX_LP_BUY_AMOUNT} COPX)",
        tx_hash=dex_col_sells_hash or None,
    )

    # Seed COPX<->COL DEX: LP sells COPX for COL at ~10:1
    dex_copx_sells_hash = create_copx_col_offer(
        client=client,
        lp_wallet=lp_w,
        taker_gets=IssuedCurrencyAmount(
            currency=COPX_HEX,
            issuer=issuer_addr,
            value=COPX_LP_SELL_AMOUNT,
        ),
        taker_pays=IssuedCurrencyAmount(
            currency=COL_CODE,
            issuer=issuer_addr,
            value=COL_LP_BUY_AMOUNT,
        ),
        verbose=args.verbose,
    )
    append_tx_note(
        txlog_path,
        f"DEX offer created (LP sells {COPX_LP_SELL_AMOUNT} COPX for {COL_LP_BUY_AMOUNT} COL)",
        tx_hash=dex_copx_sells_hash or None,
    )

    write_json(out_dir / "trustlines.json", {"currency_hex": COPX_HEX, "accounts": ["user", "lp"]})

    # Optional: snapshot COPX<->COL orderbook after seeding LP offers
    orderbook = inspect_copx_col_orderbook(
        client=client,
        issuer_addr=issuer_addr,
        verbose=args.verbose,
    )
    write_json(out_dir / "orderbook_copx_col.json", orderbook)
    append_tx_note(txlog_path, "orderbook snapshot captured (COPX<->COL)")

    # Derive offer count for bridge state snapshot
    offers = []
    if isinstance(orderbook, dict):
        offers = orderbook.get("offers", []) or []

    # Simulate a small COL->COPX bridge payment (user self-payment)
    bridge_hash = simulate_col_to_copx_payment(
        client=client,
        user_wallet=user_w,
        issuer_addr=issuer_addr,
        amount_copx="1000",
        max_col_spend="2000",
        verbose=args.verbose,
    )
    bridge_status = "ok" if bridge_hash else "error_or_no_path"
    append_tx_note(
        txlog_path,
        "bridge payment simulated (COL->COPX, user self-payment, 1000 COPX)",
        tx_hash=bridge_hash or None,
    )

    bridge_state = {
        "network": args.network,
        "issuer": issuer_addr,
        "user": user_rec["address"],
        "lp": lp_rec["address"],
        "copx_hex": COPX_HEX,
        "col_code": COL_CODE,
        "orderbook_offers": len(offers),
        "bridge_status": bridge_status,
        "bridge_tx_hash": bridge_hash or None,
    }
    write_json(out_dir / "bridge_state.json", bridge_state)
    append_tx_note(txlog_path, "bridge state snapshot written")

    # Snapshot COPX/COL balances (user + LP) for simulation
    def _snapshot_addr(addr: str) -> dict:
        info = client.request(
            AccountInfo(
                account=addr,
                ledger_index="validated",
                strict=True,
            )
        ).result
        xrp_drops = (info.get("account_data") or {}).get("Balance")
        xrp = None
        if xrp_drops is not None:
            try:
                xrp = str(Decimal(xrp_drops) / Decimal("1000000"))
            except Exception:
                xrp = xrp_drops

        lines_resp = client.request(AccountLines(account=addr)).result
        lines = lines_resp.get("lines", [])
        ious = []
        for line in lines:
            if line.get("account") == issuer_addr and line.get("currency") in (COPX_HEX, COL_CODE):
                ious.append(
                    {
                        "currency": line.get("currency"),
                        "balance": line.get("balance"),
                        "limit": line.get("limit"),
                    }
                )
        return {"xrp": xrp, "ious": ious}

    balances = {
        "issuer": {"address": issuer_addr},
        "user": {
            "address": user_rec["address"],
            **_snapshot_addr(user_rec["address"]),
        },
        "lp": {
            "address": lp_rec["address"],
            **_snapshot_addr(lp_rec["address"]),
        },
    }
    write_json(out_dir / "balances_copx_col.json", balances)
    append_tx_note(txlog_path, "balances snapshot written (COPX/COL user+lp)")

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
        "",
        "Artifacts:",
        " - orderbook: orderbook_copx_col.json",
        " - bridge state: bridge_state.json",
        " - balances: balances_copx_col.json",
    ]
    human_path.write_text("\n".join(summary_lines), encoding="utf-8")

    append_tx_note(txlog_path, "bootstrap finished")
    return 0


def inspect_copx_col_orderbook(
    client: JsonRpcClient,
    issuer_addr: str,
    verbose: bool = False,
) -> dict:
    """
    Inspect the COPX<->COL orderbook (COPX -> COL side) for this issuer.
    Returns the raw result dict from the BookOffers request.
    """
    req = BookOffers(
        taker_gets={
            "currency": COPX_HEX,
            "issuer": issuer_addr,
        },
        taker_pays={
            "currency": COL_CODE,
            "issuer": issuer_addr,
        },
        limit=20,
    )
    resp = client.request(req)
    result = getattr(resp, "result", None) or resp
    offers = []
    if isinstance(result, dict):
        offers = result.get("offers", [])
    if verbose:
        print(f"[orderbook] COPX->COL offers: {len(offers)}")
    return result if isinstance(result, dict) else {"offers": offers}


def simulate_col_to_copx_payment(
    client: JsonRpcClient,
    user_wallet: Wallet,
    issuer_addr: str,
    amount_copx: str = "1000",
    max_col_spend: str = "200",
    verbose: bool = False,
) -> str:
    """
    Simulate a COL -> COPX bridge payment:
    - Source: user_wallet (pays in COL_CODE).
    - Destination: user_wallet (self-payment, receives COPX_HEX).
    - amount_copx: how much COPX the destination should receive.
    - max_col_spend: max COL the user is willing to spend.
    """
    tx = Payment(
        account=user_wallet.classic_address,
        destination=user_wallet.classic_address,
        amount=IssuedCurrencyAmount(
            currency=COPX_HEX,
            issuer=issuer_addr,
            value=amount_copx,
        ),
        send_max=IssuedCurrencyAmount(
            currency=COL_CODE,
            issuer=issuer_addr,
            value=max_col_spend,
        ),
    )
    if verbose:
        print(
            "[bridge] user "
            f"{user_wallet.classic_address} pays up to {max_col_spend} {COL_CODE} "
            f"to deliver {amount_copx} {COPX_HEX} to {issuer_addr}"
        )

    tx_prepared = autofill(tx, client)
    signed = sign(tx_prepared, user_wallet)
    try:
        result = submit_and_wait(signed, client)
    except Exception as e:
        if verbose:
            print(f"[bridge] ERROR during COL->COPX payment: {e}")
        return ""

    tx_result = (getattr(result, "result", None) or result)
    tx_hash = None
    if isinstance(tx_result, dict):
        tx_hash = (tx_result.get("tx_json") or {}).get("hash") or tx_result.get("hash")

    if verbose:
        print(f"[bridge] submitted COL->COPX payment, hash={tx_hash}")

    return tx_hash or ""


if __name__ == "__main__":
    sys.exit(main())




























