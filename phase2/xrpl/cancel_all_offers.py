import os, argparse, json, sys
from typing import List, Dict, Any

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountInfo, AccountOffers
from xrpl.models.transactions import OfferCancel
from xrpl.transaction import autofill_and_sign, submit_and_wait

COPX160 = "434F505800000000000000000000000000000000"  # "COPX"

def to160(code: str) -> str:
    c = (code or "").strip().upper()
    if len(c) == 40 and all(ch in "0123456789ABCDEF" for ch in c):
        return c
    if len(c) <= 20 and c.isascii():
        # pad ASCII bytes of code to 20 bytes, then hex
        b = c.encode("ascii")
        if len(b) > 20:
            raise ValueError("Currency code too long for 160-bit code.")
        return (b + b"\x00" * (20 - len(b))).hex().upper()
    raise ValueError("Unsupported currency code format; supply 3-20 ASCII chars or 40-hex 160-bit.")

def is_issued_obj(v: Any) -> bool:
    return isinstance(v, dict) and "currency" in v and "issuer" in v

def offer_matches_filter(offer: Dict[str, Any], code160: str, issuer: str) -> bool:
    for side in ("taker_gets", "taker_pays"):
        v = offer.get(side)
        if is_issued_obj(v):
            cur = str(v.get("currency"))
            iss = str(v.get("issuer"))
            if cur.upper() == code160.upper() and iss == issuer:
                return True
    return False

def main():
    ap = argparse.ArgumentParser(description="Cancel open offers for an account (optionally filtered by issued currency).")
    ap.add_argument("--issuer", help="Issuer classic address for filter (required with --only-currency).")
    ap.add_argument("--only-currency", help="Filter to this currency only (e.g. COPX or 160-bit hex).")
    ap.add_argument("--seed-env", default="", help="Env var name holding the seed (default: BIDDER_SEED, fallback: TAKER_SEED).")
    ap.add_argument("--dry-run", action="store_true", help="List what would be canceled, but do not submit cancels.")
    ap.add_argument("--max", type=int, default=500, help="Max offers to cancel this run.")
    args = ap.parse_args()

    # RPC + seed
    rpc = os.environ.get("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    seed = None
    if args.seed_env:
        seed = os.environ.get(args.seed_env)
    if not seed:
        seed = os.environ.get("BIDDER_SEED") or os.environ.get("TAKER_SEED")
    if not seed:
        print("Missing seed: set BIDDER_SEED or TAKER_SEED (or use --seed-env NAME).", file=sys.stderr)
        sys.exit(2)

    client = JsonRpcClient(rpc)
    wallet = Wallet.from_seed(seed)

    # Optional filter
    code160 = None
    issuer = None
    if args.only_currency:
        code160 = to160(args.only_currency)
        if not args.issuer:
            print("--issuer is required when using --only-currency.", file=sys.stderr)
            sys.exit(2)
        issuer = args.issuer

    # Account info (sanity)
    info = client.request(AccountInfo(account=wallet.classic_address, ledger_index="current")).result
    # Fetch open offers
    resp = client.request(AccountOffers(account=wallet.classic_address))
    offers: List[Dict[str, Any]] = resp.result.get("offers", [])

    # Filter
    selected: List[Dict[str, Any]] = []
    for off in offers:
        if code160 and issuer:
            if offer_matches_filter(off, code160, issuer):
                selected.append(off)
        else:
            selected.append(off)

    if not selected:
        print(json.dumps({"account": wallet.classic_address, "selected": 0, "canceled": 0, "dry_run": args.dry_run}, indent=2))
        return

    # Trim to --max
    selected = selected[: max(1, args.max)]

    summary = {
        "account": wallet.classic_address,
        "rpc": rpc,
        "total_offers": len(offers),
        "selected_count": len(selected),
        "dry_run": args.dry_run,
        "cancels": []
    }

    if args.dry_run:
        for off in selected:
            summary["cancels"].append({"offer_sequence": off.get("seq"), "summary": {
                "taker_gets": off.get("taker_gets"), "taker_pays": off.get("taker_pays")
            }})
        print(json.dumps(summary, indent=2))
        return

    # Submit OfferCancel for each selected offer
    for off in selected:
        seq = off.get("seq")
        tx = OfferCancel(
            account=wallet.classic_address,
            offer_sequence=seq,
        )
        signed = autofill_and_sign(tx, client, wallet)
        res = submit_and_wait(signed, client).result
        summary["cancels"].append({
            "offer_sequence": seq,
            "result": res.get("engine_result"),
            "hash": res.get("tx_json", {}).get("hash") or res.get("hash"),
            "ledger_index": res.get("ledger_index"),
        })

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
