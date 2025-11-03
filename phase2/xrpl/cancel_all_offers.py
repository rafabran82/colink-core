import os, argparse, json, sys, time
from typing import List, Dict, Any
import requests

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountInfo, AccountOffers
from xrpl.models.transactions import OfferCancel
from xrpl.transaction import autofill_and_sign
from xrpl.core.binarycodec import encode as encode_tx

# --- sha512_half import fallback (handles different xrpl-py versions) ---
try:
    # newer xrpl-py
    from xrpl.core.binarycodec.hashing import sha512_half as _sha512_half
    def sha512half(data: bytes) -> bytes:
        return _sha512_half(data)
except Exception:
    # minimal local fallback
    import hashlib
    def sha512half(data: bytes) -> bytes:
        return hashlib.sha512(data).digest()[:32]

COPX160 = "434F505800000000000000000000000000000000"  # "COPX" 160-bit

def to160(code: str) -> str:
    c = (code or "").strip().upper()
    if len(c) == 40 and all(ch in "0123456789ABCDEF" for ch in c):
        return c
    if len(c) <= 20 and c.isascii():
        b = c.encode("ascii")
        if len(b) > 20:
            raise ValueError("Currency code too long for 160-bit code.")
        return (b + b"\x00" * (20 - len(b))).hex().upper()
    raise ValueError("Unsupported currency code; use 3–20 ASCII chars or 40 hex.")

def is_issued(v: Any) -> bool:
    return isinstance(v, dict) and "currency" in v and "issuer" in v

def offer_matches(offer: Dict[str, Any], code160: str, issuer: str) -> bool:
    for side in ("taker_gets", "taker_pays"):
        v = offer.get(side)
        if is_issued(v):
            if str(v.get("currency")).upper() == code160.upper() and str(v.get("issuer")) == issuer:
                return True
    return False

def tx_blob_and_hash(signed_tx) -> (str, str):
    """Return (tx_blob_hex, tx_hash_hex) from a signed Transaction."""
    tx_dict = signed_tx.to_dict()
    blob = encode_tx(tx_dict)  # hex string
    # Hash = SHA512Half( 0x54584E00 || blob_bytes )   # "TXN" prefix
    prefixed = bytes.fromhex("54584E00") + bytes.fromhex(blob)
    tx_hash = sha512half(prefixed).hex().upper()
    return blob, tx_hash

def rpc_submit_blob(rpc_url: str, blob: str) -> Dict[str, Any]:
    payload = {"method": "submit", "params": [{"tx_blob": blob}]}
    r = requests.post(rpc_url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("result", data)

def rpc_tx(rpc_url: str, tx_hash: str) -> Dict[str, Any]:
    payload = {"method": "tx", "params": [{"transaction": tx_hash, "binary": False}]}
    r = requests.post(rpc_url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("result", data)

def submit_and_poll_raw(rpc_url: str, signed_tx) -> Dict[str, Any]:
    """Submit signed blob via raw JSON-RPC and poll until validated (or timeout)."""
    blob, local_hash = tx_blob_and_hash(signed_tx)
    prelim = rpc_submit_blob(rpc_url, blob)
    tx_hash = (prelim.get("tx_json", {}) or {}).get("hash") or prelim.get("hash") or local_hash

    out = {"prelim": prelim, "hash": tx_hash}
    for _ in range(20):  # ~40s
        if not tx_hash:
            break
        res = rpc_tx(rpc_url, tx_hash)
        out["tx"] = res
        if res.get("validated"):
            return out
        time.sleep(2)
    return out

def main():
    ap = argparse.ArgumentParser(description="Cancel open offers (optionally filter by issued currency).")
    ap.add_argument("--issuer", help="Issuer classic address when using --only-currency.")
    ap.add_argument("--only-currency", help="Filter to this currency (e.g., COPX or 160-bit hex).")
    ap.add_argument("--seed-env", default="", help="Env var name for seed; default BIDDER_SEED/TAKER_SEED.")
    ap.add_argument("--dry-run", action="store_true", help="List what would be canceled; do not submit.")
    ap.add_argument("--max", type=int, default=500, help="Max offers to cancel this run.")
    ap.add_argument("--no-wait", action="store_true", help="Submit cancels but do not poll for validation.")
    args = ap.parse_args()

    rpc = os.environ.get("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    seed = os.environ.get(args.seed_env) if args.seed_env else None
    if not seed:
        seed = os.environ.get("BIDDER_SEED") or os.environ.get("TAKER_SEED")
    if not seed:
        print("Missing seed: set BIDDER_SEED or TAKER_SEED (or --seed-env).", file=sys.stderr)
        sys.exit(2)

    client = JsonRpcClient(rpc)
    wallet = Wallet.from_seed(seed)

    code160 = issuer = None
    if args.only_currency:
        code160 = to160(args.only_currency)
        if not args.issuer:
            print("--issuer is required with --only-currency.", file=sys.stderr); sys.exit(2)
        issuer = args.issuer

    _ = client.request(AccountInfo(account=wallet.classic_address, ledger_index="current")).result
    offers = client.request(AccountOffers(account=wallet.classic_address)).result.get("offers", [])

    selected: List[Dict[str, Any]] = []
    for off in offers:
        if code160 and issuer:
            if offer_matches(off, code160, issuer):
                selected.append(off)
        else:
            selected.append(off)
    selected = selected[: max(1, args.max)]

    summary = {
        "account": wallet.classic_address,
        "rpc": rpc,
        "total_offers": len(offers),
        "selected_count": len(selected),
        "dry_run": args.dry_run,
        "results": []
    }

    if args.dry_run or not selected:
        for off in selected:
            summary["results"].append({
                "offer_sequence": off.get("seq"),
                "preview": {"taker_gets": off.get("taker_gets"), "taker_pays": off.get("taker_pays")}
            })
        print(json.dumps(summary, indent=2))
        return

    for off in selected:
        seq = off.get("seq")
        tx = OfferCancel(account=wallet.classic_address, offer_sequence=seq)
        signed = autofill_and_sign(tx, client, wallet)
        if args.no_wait:
            blob, local_hash = tx_blob_and_hash(signed)
            prelim = rpc_submit_blob(rpc, blob)
            tx_hash = (prelim.get("tx_json", {}) or {}).get("hash") or prelim.get("hash") or local_hash
            summary["results"].append({
                "offer_sequence": seq,
                "mode": "submitted_no_wait",
                "prelim_engine": prelim.get("engine_result"),
                "hash": tx_hash
            })
        else:
            outcome = submit_and_poll_raw(rpc, signed)
            tx_res = outcome.get("tx", {})
            prelim = outcome.get("prelim", {})
            summary["results"].append({
                "offer_sequence": seq,
                "mode": "submitted_and_polled",
                "prelim_engine": prelim.get("engine_result"),
                "hash": outcome.get("hash"),
                "validated": tx_res.get("validated"),
                "meta_result": (tx_res.get("meta", {}) or {}).get("TransactionResult"),
                "ledger_index": tx_res.get("ledger_index"),
            })

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()

