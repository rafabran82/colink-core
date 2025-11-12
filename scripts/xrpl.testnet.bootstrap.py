#!/usr/bin/env python3
"""
XRPL Testnet Bootstrap — Modules 1 + 2
Phase: Imports + Constants + JSON helpers
"""

import sys
import json
import time
import logging
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet

# === Constants ===
JSON_RPC_TESTNET = "https://s.altnet.rippletest.net:51234"
CURRENCY_CODE = "COPX"


# ============================================================
# Module 2 — JSON helpers
# ============================================================

def _write_json(path: Path, obj) -> None:
    """Safely write a JSON file with pretty formatting."""
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _append_tx_note(path: Path, note: str) -> None:
    """Append a timestamped NDJSON line."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = {"ts": ts, "note": str(note)}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
