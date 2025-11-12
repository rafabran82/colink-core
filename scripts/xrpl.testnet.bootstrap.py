#!/usr/bin/env python3
"""
XRPL Testnet Bootstrap — Modules 1–3
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


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)

    # args: --network testnet --out dir --execute --verbose (we’ll parse in later modules)
    out_dir = Path(".artifacts/data/bootstrap")
    out_dir.mkdir(parents=True, exist_ok=True)

    txlog_path = out_dir / "tx_log.ndjson"
    if not txlog_path.exists():
        txlog_path.write_text("", encoding="utf-8")
        _append_tx_note(txlog_path, "bootstrap init")

    wallets_path = out_dir / "wallets.json"
    if not wallets_path.exists():
        _write_json(wallets_path, {"issuer": None, "user": None, "lp": None})

    trust_path = out_dir / "trustlines.json"
    if not trust_path.exists():
        _write_json(trust_path, [])

    offers_path = out_dir / "offers.json"
    if not offers_path.exists():
        _write_json(offers_path, [])

    return 0


if __name__ == "__main__":
    sys.exit(main())
