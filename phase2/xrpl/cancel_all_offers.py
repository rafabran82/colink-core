import os, json, time, argparse, requests
from hashlib import sha512
from typing import List, Dict, Any, Optional

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountOffers, AccountInfo
from xrpl.models.transactions import OfferCancel
from xrpl.transaction import autofill_and_sign
from xrpl.core.binarycodec import encode as encode_tx

TX_PREFIX = bytes.fromhex("54584E00")  # 'TXN' + 0x00

def sha512half(b: bytes) -> bytes:
    return sha512(b).digest()[:32]

def env_first(*keys: str) -> Optional[str]:
    for k in keys:
        v = os.environ.get(k)
        if v:
            return v
    return None

def get_account_info(client: JsonRpcClient, addr: str) -> Dict[str, Any]:
    return client.request(AccountInfo(account=addr, ledger_index="validated")).result

def get_offers(client: JsonRpcClient, addr: str, limit: int = 500) -> List[Dict[str, Any]]:
    res = client.request(AccountOffers(account=addr, ledger_index="validated", limit=limit)).result
    return res.get("offers", [])

def filter_copx_offers(offers: List[Dict[str, Any]], issuer: str, code160: str) -> List[Dict[str, Any]]:
    out = []
    for o in offers:
        tg = o.get("taker_gets")
        tp = o.get("taker_pays")
        def is_copx(x):
            return isinstance(x, dict) and x.get("currency") == code160 and x.get("issuer") == issuer
        if is_copx(tg) or is_copx(tp):
            out.append(o)
    return out

def choose_seed_from_env(pref: Optional[str]) -> str:
    if pref:
        v = os.environ.get(pref)
        if v: return v
    # fallbacks
    for k in ("XRPL_TAKER_SEED","XRPL_MAKER_SEED","XRPL_HOT_SEED","XRPL_ISSUER_SEED","TAKER_SEED","BIDDER_SEED"):
        v = os.environ.get(k)
        if v: return v
    raise SystemExit("No seed found in environment (XRPL_*_SEED / TAKER_SEED / BIDDER_SEED).")

def tx_blob_and_hash(signed_tx) -> (str, str):
    """
    Prefer the already-signed blob if present (newer xrpl-py).
    Otherwise encode the canonical XRPL JSON (not snake_case) to hex.
    """
    blob = getattr(signed_tx, "signed_transaction_blob", None)
    if not blob:
        # encode using canonical XRPL JSON (camel-cased keys) to avoid KeyError: 'account'
        tx_json = signed_tx.to_xrpl() if hasattr(signed_tx, "to_xrpl") else signed_tx
        blob = encode_tx(tx_json)
    hx = sha512half(TX_PREFIX + bytes.fromhex(blob)).hex().upper()
    return blob, hx

def submit_blob(rpc_url: str, blob_hex: str) -> Dict[str, Any]:
    payload = {"method":"submit","params":[{"tx_blob": blob_hex}]}
    r = requests.post(rpc_url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("result", {})

def tx_result_by_hash(rpc_url: str, tx_hash: str) -> Dict[str, Any]:
    payload = {"method":"tx","params":[{"transaction": tx_hash, "binary": False}]}
    r = requests.post(rpc_url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("result", {})

def submit_and_poll_raw(rpc_url: str, signed_tx, max_wait_s: int = 20) -> Dict[str, Any]:
    blob, local_hash = tx_blob_and_hash(signed_tx)
    prelim = submit_blob(rpc_url, blob)
    out = {
        "mode": "submitted_and_polled",
        "prelim_engine": prelim.get("engine_result"),
        "hash": local_hash,
        "validated": None,
        "meta_result": None,
        "ledger_index": None,
    }
    # quick poll loop
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        time.sleep(1.5)
        txr = tx_result_by_hash(rpc_url, local_hash)
        if txr.get("validated"):
            out["validated"] = True
            out["meta_result"] = (txr.get("meta") or {}).get("TransactionResult")
            out["ledger_index"] = txr.get("ledger_index")
            return out
    return out  # not validated yet

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issuer", help="Issuer classic address for COPX filter")
    ap.add_argument("--only-currency", choices=["COPX"], help="If set, restrict cancels to this currency")
    ap.add_argument("--seed-env", help="Pick a specific env var name for the seed (else fallback chain)")
    ap.add_argument("--max", type=int, default=500)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    args = ap.parse_args()

    rpc = os.environ.get("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    seed = choose_seed_from_env(args.seed_env)
    wallet = Wallet.from_seed(seed)
    client = JsonRpcClient(rpc)

    acct = wallet.classic_address
    offers = get_offers(client, acct, limit=args.max)

    selected = offers
    if args.only_currency == "COPX":
        if not args.issuer:
            raise SystemExit("--issuer is required with --only-currency COPX")
        code160 = "434F505800000000000000000000000000000000"
        selected = filter_copx_offers(offers, args.issuer, code160)

    summary = {
        "account": acct,
        "rpc": rpc,
        "total_offers": len(offers),
        "selected_count": len(selected),
        "dry_run": bool(args.dry_run),
        "results": []
    }

    if args.dry_run:
        for o in selected:
            preview = {
                "taker_gets": o.get("taker_gets"),
                "taker_pays": o.get("taker_pays")
            }
            summary["results"].append({
                "offer_sequence": o.get("seq"),
                "preview": preview
            })
        print(json.dumps(summary, indent=2))
        return

    # build & sign
    signed_list = []
    for o in selected:
        oc = OfferCancel(
            account=acct,
            offer_sequence=o.get("seq"),
        )
        signed = autofill_and_sign(oc, client, wallet)
        signed_list.append((o, signed))

    # submit
    for o, signed in signed_list:
        if args.no_wait:
            blob, local_hash = tx_blob_and_hash(signed)
            prelim = submit_blob(rpc, blob)
            summary["results"].append({
                "offer_sequence": o.get("seq"),
                "mode": "submitted_no_wait",
                "prelim_engine": prelim.get("engine_result"),
                "hash": local_hash
            })
        else:
            outcome = submit_and_poll_raw(rpc, signed)
            summary["results"].append({
                "offer_sequence": o.get("seq"),
                **outcome
            })

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
