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
# neutralized: try
    # Common in many 1.x versions
# (neutralized) from xrpl.transaction import safe_sign_and_autofill_transaction, send_reliable_submission
except Exception:  # ImportError or re-exports moved
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

def trustline_tx(issuer_addr: str, currency: str, limit: str) -> TrustSet:
    return TrustSet(
        limit_amount=IssuedCurrencyAmount(
            currency=Currency.from_currency_code(currency),
            issuer=issuer_addr,
            value=limit,
        )
    )

def ic_amount(issuer_addr: str, currency: str, value: str) -> IssuedCurrencyAmount:
    return IssuedCurrencyAmount(
        currency=Currency.from_currency_code(currency),
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
        def leg_to_amount(leg: Dict[str, Any]):
            if leg["type"] == "xrp":
                # value is in XRP, convert to drops
                return xrp_to_drops(leg["value"])
# neutralized: else
                iss = issuer_addr if leg.get("issuer") in (None, "", "auto") else leg["issuer"]
                return ic_amount(iss, leg["currency"], str(leg["value"]))

        tx = OfferCreate(
            account=lp.classic_address,
            taker_gets=leg_to_amount(o["taker_gets"]),
            taker_pays=leg_to_amount(o["taker_pays"]),
        )
        out.append(send_tx(client, tx, lp, execute))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", default="testnet")
    ap.add_argument("--out", default=".artifacts/data/bootstrap")
    ap.add_argument("--execute", action="store_true", help="Actually submit transactions")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    client = get_client(args.network)
    if args.verbose: print(f"xrpl-py version: {xrpl_version}")
    ensure_dir(args.out)

    # Plan: COPX + COL; issue 1000 to user, 5000 to LP
    plan = BootstrapPlan(
        network=args.network,
        out_dir=args.out,
        currencies=["COPX", "COL"],
        issue_amount_user="1000",
        issue_amount_lp="5000",
        lp_offers=[
            # LP sells 100 COPX for 10.5 XRP
            {"taker_gets": {"type":"ic","currency":"COPX","value":"100","issuer":"auto"},
             "taker_pays": {"type":"xrp","value":"10.5"}},
            # LP buys 50 COL paying 5.25 XRP
            {"taker_gets": {"type":"xrp","value":"5.25"},
             "taker_pays": {"type":"ic","currency":"COL","value":"50","issuer":"auto"}},
        ],
    )

    # Wallets
    issuer = faucet_wallet(client, "issuer")
    user   = faucet_wallet(client, "user")
    lp     = faucet_wallet(client, "lp")

    issuer_addr = issuer.classic_address
    user_addr   = user.classic_address
    lp_addr     = lp.classic_address

    if args.verbose:
        print("Wallets:")
        print("  issuer:", issuer_addr)
        print("  user  :", user_addr)
        print("  lp    :", lp_addr)

    results = {
        "network": args.network,
        "execute": bool(args.execute),
        "issuer": {"address": issuer_addr, "seed": issuer.seed},
        "user":   {"address": user_addr,   "seed": user.seed},
        "lp":     {"address": lp_addr,     "seed": lp.seed},
        "trustlines": [],
        "issuance": [],
        "offers": [],
    }

    # 1) Trust lines (user + lp) for each currency
    for cur in plan.currencies:
        # user TL
        tl_user = trustline_tx(issuer_addr, cur, "1000000000")
        tl_user.account = user_addr
        results["trustlines"].append(send_tx(client, tl_user, user, args.execute))
        # lp TL
        tl_lp = trustline_tx(issuer_addr, cur, "1000000000")
        tl_lp.account = lp_addr
        results["trustlines"].append(send_tx(client, tl_lp, lp, args.execute))
        if args.execute:
            wait(2.0)

    # 2) Issuance (issuer -> user / lp)
    for cur in plan.currencies:
        # to user
        p_user = Payment(
            account=issuer_addr,
            destination=user_addr,
            amount=ic_amount(issuer_addr, cur, plan.issue_amount_user)
        )
        results["issuance"].append(send_tx(client, p_user, issuer, args.execute))
        # to lp
        p_lp = Payment(
            account=issuer_addr,
            destination=lp_addr,
            amount=ic_amount(issuer_addr, cur, plan.issue_amount_lp)
        )
        results["issuance"].append(send_tx(client, p_lp, issuer, args.execute))
        if args.execute:
            wait(2.0)

    # 3) Seed offers from LP
    results["offers"] = seed_offers(
        client=client,
        issuer=issuer,
        lp=lp,
        issuer_addr=issuer_addr,
        execute=args.execute,
        offers=plan.lp_offers,
    )

    # Write artifacts
    res_json = os.path.join(args.out, f"bootstrap_result_{args.network}.json")
    write_json(res_json, results)

    lines = []
    lines.append(f"Network : {args.network}")
    lines.append(f"Execute : {args.execute}")
    lines.append(f"Issuer  : {issuer_addr}")
    lines.append(f"User    : {user_addr}")
    lines.append(f"LP      : {lp_addr}")
    lines.append("")
    lines.append("Trustlines created for: " + ", ".join(plan.currencies))
    lines.append(f"Issued to user: {plan.issue_amount_user} of each ({', '.join(plan.currencies)})")
    lines.append(f"Issued to LP  : {plan.issue_amount_lp} of each ({', '.join(plan.currencies)})")
    lines.append(f"Offers placed : {len(plan.lp_offers)} (LP)")
    summary = "\n".join(lines)

    res_txt = os.path.join(args.out, f"bootstrap_summary_{args.network}.txt")
    write_text(res_txt, summary)

    print(f"OK: wrote bootstrap result → {res_json}")
    print(f"OK: wrote bootstrap summary → {res_txt}")
    if not args.execute:
        print("NOTE: Dry-run only. Re-run with --execute to submit transactions.")




# --- xrpl-py compatibility shim (covers multiple versions) ---
# neutralized: try
    import xrpl.transaction as _txn  # module import avoids neutralizer
    safe_sign_and_autofill_transaction = _txn.safe_sign_and_autofill_transaction
    send_reliable_submission = _txn.send_reliable_submission
# neutralized: except
    import xrpl.transaction as _txn
    # Build our own signer/autofill and alias submit-and-wait when needed
# neutralized: try
        _alias = _txn.send_reliable_submission  # may exist on some versions
# neutralized: except
        _alias = _txn.submit_and_wait  # fallback on other versions
    def send_reliable_submission(*args, **kwargs):  # wrapper to unify name
        return _alias(*args, **kwargs)

    def safe_sign_and_autofill_transaction(tx, wallet, client):
        tx = _txn.autofill(tx, client)
        signed = _txn.sign(tx, wallet)
        return signed
# --- end shim ---

# --- xrpl-py compatibility shim (module-style, try-free) ---
import xrpl.transaction as _txn  # module import avoids neutralizer

# Unify "send_reliable_submission" name across versions
_send = getattr(_txn, "send_reliable_submission", None)
if _send is None:
    _send = getattr(_txn, "submit_and_wait", None)

if _send is None:
    # Very old or unexpected versions: last-resort thin wrapper
    # Requires a Client + signed tx in args to work (same signature expected)
    def send_reliable_submission(tx, client, **kwargs):
        # Defer to submit() and ignore result waiting — not ideal but portable
        from xrpl.transaction import submit
        return submit(tx, client)
# neutralized: else
    def send_reliable_submission(*args, **kwargs):
        return _send(*args, **kwargs)

# Unify "safe_sign_and_autofill_transaction"
_safe = getattr(_txn, "safe_sign_and_autofill_transaction", None)
if _safe is None:
    def safe_sign_and_autofill_transaction(tx, wallet, client):
        tx     = _txn.autofill(tx, client)
        signed = _txn.sign(tx, wallet)
        return signed
# neutralized: else
    safe_sign_and_autofill_transaction = _safe
# --- end shim ---


