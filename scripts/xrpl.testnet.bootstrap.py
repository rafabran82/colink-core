#!/usr/bin/env python3
"""
XRPL Testnet Bootstrap — Modules 1–4
"""

import sys
import json
import time
import logging
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet

JSON_RPC_TESTNET = "https://s.altnet.rippletest.net:51234"
CURRENCY_CODE = "COPX"


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _append_tx_note(path: Path, note: str) -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = {"ts": ts, "note": str(note)}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _ensure_wallets(out_dir: Path, txlog_path: Path):
    wallets_path = out_dir / "wallets.json"
    wallets = json.loads(wallets_path.read_text(encoding="utf-8"))

    def _create(name):
        w = Wallet.create()
        wallets[name] = {
            "address": w.classic_address,
            "seed": w.seed,
            "public": w.public_key,
            "private": w.private_key,
        }
        _append_tx_note(txlog_path, f"created wallet: {name}")

    if wallets.get("issuer") is None:
        _create("issuer")

    if wallets.get("user") is None:
        _create("user")

    if wallets.get("lp") is None:
        _create("lp")

    _write_json(wallets_path, wallets)
    return wallets


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)

    out_dir = Path(".artifacts/data/bootstrap")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ensure tx log exists
    txlog_path = out_dir / "tx_log.ndjson"
    if not txlog_path.exists():
        txlog_path.write_text("", encoding="utf-8")
        _append_tx_note(txlog_path, "bootstrap init")

    # Ensure base files
    if not (out_dir / "wallets.json").exists():
        _write_json(out_dir / "wallets.json", {"issuer": None, "user": None, "lp": None})

    if not (out_dir / "trustlines.json").exists():
        _write_json(out_dir / "trustlines.json", [])

    if not (out_dir / "offers.json").exists():
        _write_json(out_dir / "offers.json", [])

    # --- MODULE 4: generate wallets ---
    wallets = _ensure_wallets(out_dir, txlog_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
