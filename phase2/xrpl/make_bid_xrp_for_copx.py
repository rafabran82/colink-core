import os, argparse, json
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import autofill_and_sign, submit_and_wait

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issuer", required=True)
    ap.add_argument("--value",  type=str, required=True, help="COPX you want to BUY")
    ap.add_argument("--drops",  type=str, required=True, help="XRP drops you will PAY")
    args = ap.parse_args()

    rpc = os.environ.get("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    seed = os.environ.get("BIDDER_SEED") or os.environ.get("TAKER_SEED")
    if not seed:
        raise SystemExit("Missing BIDDER_SEED (or TAKER_SEED) in environment.")

    client = JsonRpcClient(rpc)
    wallet = Wallet.from_seed(seed)

    # BUY COPX (TakerGets = COPX), PAY XRP (TakerPays = drops)
    tx = OfferCreate(
        account=wallet.classic_address,
        taker_gets={
            "currency": "434F505800000000000000000000000000000000",
            "issuer": args.issuer,
            "value":  args.value,
        },
        taker_pays=args.drops,  # drops of XRP
    )
    signed = autofill_and_sign(tx, client, wallet)
    resp = submit_and_wait(signed, client)
    print(json.dumps(resp.result, indent=2))
    h = resp.result.get("hash")
    if h: print(f"\nExplorer: https://testnet.xrpl.org/transactions/{h}")

if __name__ == "__main__":
    main()
