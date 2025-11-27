import argparse
import time
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import Payment
from xrpl.models.requests import Tx
from xrpl.transaction import sign_and_submit

def wait_for_validation(client, tx_hash, timeout=20):
    for _ in range(timeout):
        resp = client.request(Tx(transaction=tx_hash))
        if resp.result.get("validated"):
            return resp.result
        time.sleep(1)
    return {"error": "Timeout waiting for validation", "hash": tx_hash}

def issue_iou(seed, destination, currency_hex, amount, rpc):
    client = JsonRpcClient(rpc)
    wallet = Wallet.from_seed(seed)

    amt = IssuedCurrencyAmount(
        issuer=wallet.classic_address,
        currency=currency_hex,
        value=str(amount)
    )

    tx = Payment(
        account=wallet.classic_address,
        amount=amt,
        destination=destination
    )

    # Submit the transaction
    submit_result = sign_and_submit(tx, client, wallet)
    tx_hash = submit_result.result.get("tx_json", {}).get("hash")

    # Wait for validation
    final = wait_for_validation(client, tx_hash)
    return final

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--amount", required=True)
    parser.add_argument("--rpc", required=True)
    args = parser.parse_args()

    # COPX 160-bit HEX code
    currency_hex = "43504F5800000000000000000000000000000000"

    result = issue_iou(
        args.seed,
        args.destination,
        currency_hex,
        args.amount,
        args.rpc
    )

    print(result)

if __name__ == "__main__":
    main()
