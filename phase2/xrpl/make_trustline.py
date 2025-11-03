import os, argparse, json
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import TrustSet
from xrpl.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.currencies import IssuedCurrency

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--issuer", required=True)
    p.add_argument("--currency", default="COPX")
    p.add_argument("--limit", default="1000000")  # trust 1,000,000 COPX by default
    args = p.parse_args()

    rpc = os.environ.get("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    seed = os.environ.get("BIDDER_SEED") or os.environ.get("TAKER_SEED")
    if not seed:
        raise SystemExit("Missing BIDDER_SEED (or TAKER_SEED) in environment.")

    client = JsonRpcClient(rpc)
    wallet = Wallet.from_seed(seed)

    # 160-bit currency code for "COPX"
    code160 = "434F505800000000000000000000000000000000"
    ic = IssuedCurrency(currency=code160, issuer=args.issuer)

    tx = TrustSet(
        account=wallet.classic_address,
        limit_amount={"currency": ic.currency, "issuer": ic.issuer, "value": args.limit},
    )
    signed = autofill_and_sign(tx, client, wallet)
    resp = submit_and_wait(signed, client)
    print(json.dumps(resp.result, indent=2))

if __name__ == "__main__":
    main()
