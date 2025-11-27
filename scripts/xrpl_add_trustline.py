import argparse
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--issuer', required=True)
    parser.add_argument('--currency', required=True)
    parser.add_argument('--value', default="1000000000")
    args = parser.parse_args()

    client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

    # FIX: proper wallet constructor for xrpl-py 2.3.0
    wallet = Wallet.from_seed(args.seed)

    amount = IssuedCurrencyAmount(
        currency=args.currency,
        issuer=args.issuer,
        value=args.value
    )

    tx = TrustSet(
        account=args.account,
        limit_amount=amount
    )

    tx = autofill(tx, client)
    signed = sign(tx, wallet)
    result = submit_and_wait(signed, client)

    print(result)

if __name__ == "__main__":
    main()
