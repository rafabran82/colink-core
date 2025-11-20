from xrpl.utils.xrp_conversions import xrp_to_drops
from decimal import Decimal
def _encode_currency_code(code: str) -> str:
    """
    XRPL currency rules:
      - If 3-letter uppercase (and not XRP), keep as-is.
      - Else encode to 160-bit hex (ASCII→hex, right-pad to 40 chars).
    """
    if isinstance(code, str):
        cc = code.strip().upper()
        if len(cc) == 3 and cc != "XRP":
            return cc
        try:
            raw = cc.encode("ascii", "strict")
        except Exception:
            raw = code.encode("utf-8", "ignore")
        hexs = raw.hex().upper()
        return hexs[:40].ljust(40, "0")
    return "COL"

#!/usr/bin/env python3
"""
XRPL Testnet Bootstrap
- Dry-run by default. Use --execute to submit transactions.
- Creates issuer/user/lp wallets, trust lines for COPX and COL,
  issues tokens to user/lp, and seeds light DEX offers.

Outputs:
  <out>/bootstrap_result_<network>.json
  <out>/bootstrap_summary_<network>.txt
"""
import argparse, json, os, time
from dataclasses import asdict, dataclass
from typing import Dict, Any, List, Optional

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.models.transactions import TrustSet, Payment, OfferCreate
from xrpl.models.requests import AccountInfo
from xrpl_compat import safe_sign_and_autofill_transaction, send_reliable_submission
# neutralized: try
    # Common in many 1.x versions
# (neutralized) from xrpl.transaction import safe_sign_and_autofill_transaction, send_reliable_submission
# neutralized: except
    # Fallback used by newer/other layouts
# (neutralized) from xrpl.helpers import safe_sign_and_autofill_transaction, send_reliable_submission
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.currencies import Currency
from xrpl.utils import xrp_to_drops
import xrpl
xrpl_version = getattr(xrpl, "__version__", "unknown")
TESTNET_JSONRPC = "https://s.altnet.rippletest.net:51234"

@dataclass
class BootstrapPlan:
    network: str
    out_dir: str
    currencies: List[str]           # ["COPX","COL"]
    issue_amount_user: str          # "1000"
    issue_amount_lp: str            # "5000"
    lp_offers: List[Dict[str, Any]] # simple seeded offers

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def wait(s: float) -> None:
    time.sleep(s)

def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2)

def get_client(network: str) -> JsonRpcClient:
    # You can expand with mainnet/devnet mapping later if needed
    return JsonRpcClient(TESTNET_JSONRPC)

def faucet_wallet(client: JsonRpcClient, tag: str) -> Wallet:
    # Faucet handles funding & activation on testnet
    w = generate_faucet_wallet(client, debug=False)
    return w

def account_seq(client: JsonRpcClient, address: str) -> int:
    req = AccountInfo(account=address, ledger_index="validated", strict=True)
    resp = client.request(req).result
    return resp["account_data"]["Sequence"]

def trustline_tx(account_addr: str, issuer_addr: str, currency: str, limit: str):
    return TrustSet(
        account=account_addr,
        limit_amount=IssuedCurrencyAmount(
            currency=_encode_currency_code(currency),
            issuer=issuer_addr,
            value=limit,
        )
    )

def ic_amount(issuer_addr: str, currency: str, value: str) -> IssuedCurrencyAmount:
    return IssuedCurrencyAmount(
        currency=_encode_currency_code(currency),
        issuer=issuer_addr,
        value=value,
    )

def send_tx(client: JsonRpcClient, tx, wallet: Wallet, execute: bool) -> Dict[str, Any]:
    """Sign, autofill, and optionally submit. Always returns a structured result."""
    signed = safe_sign_and_autofill_transaction(tx, client, wallet)
    if not execute:
        # Dry-run: do not submit—return the prepared blob
        return {
            "mode": "dry-run",
            "tx_json": signed.to_xrpl(),
        }
    # Execute: reliable submission
# neutralized: try
        result = send_reliable_submission(signed, client).result
        return {
            "mode": "execute",
            "engine_result": result.get("engine_result"),
            "tx_json": result.get("tx_json"),
            "validated": result.get("validated"),
        }
# neutralized: except
        return {"mode": "execute", "error": str(e)}

def seed_offers(client: JsonRpcClient, issuer: Wallet, lp: Wallet, issuer_addr: str, execute: bool, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    offers items:
      {
        "taker_gets": {"type":"ic"|"xrp", "currency":"COPX","value":"100","issuer":"<auto>"},
        "taker_pays": {"type":"xrp"|"ic", "value":"10.5","currency":"", "issuer":"<auto>"}
      }
    Note: If "issuer" is "auto" for IC legs, we fill with issuer_addr.
    """
    out = []
    for i, o in enumerate(offers, 1):
        pass
def leg_to_amount(leg):
    """
    Convert a leg dict into an XRPL Amount:
      - XRP legs: coerce value to Decimal, then xrp_to_drops → str
      - IOU legs: IssuedCurrencyAmount with encoded currency
    Expected keys:
      XRP: {"type":"XRP","value": <xrp amount as str/num>}
      IOU: {"type":"IOU","currency": "...", "issuer": "...", "value": <str/num>}
    """
    kind = (str(leg.get("type", "")).upper())
    if kind == "XRP":
        v = leg.get("value", 0)
        try:
            dv = v if isinstance(v, Decimal) else Decimal(str(v))
        except Exception:
            dv = Decimal(0)
        return str(xrp_to_drops(dv))

    # IOU leg
    cur = str(leg.get("currency", ""))
    iss = str(leg.get("issuer", ""))
    val = str(leg.get("value", "0"))
    return IssuedCurrencyAmount(
        currency=_encode_currency_code(cur),
        issuer=iss,
        value=val
    )

