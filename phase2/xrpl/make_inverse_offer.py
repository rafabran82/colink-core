import os, argparse, json
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issuer", required=True, help="Issuer r-address for COPX")
    ap.add_argument("--value",  required=True, help="TakerGets COPX value, e.g. 1000")
    ap.add_argument("--drops",  required=True, help="TakerPays XRP (drops), e.g. 250000 for 0.25 XRP")
    args = ap.parse_args()

    rpc = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    seed = os.getenv("TAKER_SEED") or os.getenv("XRPL_TAKER_SEED") or os.getenv("SEED")
    if not seed:
        raise SystemExit("Missing TAKER_SEED in environment.")

    client = JsonRpcClient(rpc)
    wallet = Wallet.from_seed(seed)

    copx_hex = "434F505800000000000000000000000000000000"  # 'COPX'
    taker_gets = IssuedCurrencyAmount(currency=copx_hex, issuer=args.issuer, value=str(args.value))

    tx = OfferCreate(
        account=wallet.classic_address,
        taker_gets=taker_gets,            # SELL COPX
        taker_pays=str(int(args.drops)),  # ASK XRP (drops)
        flags=0,
    )

    # Version-agnostic flow
    tx_filled = autofill(tx, client)
    tx_signed = sign(tx_filled, wallet)
    resp = submit_and_wait(tx_signed, client)

    print(json.dumps(resp.result, indent=2))
    h = resp.result.get("hash")
    if h:
        print(f"\nExplorer: https://testnet.xrpl.org/transactions/{h}")

if __name__ == "__main__":
    main()
