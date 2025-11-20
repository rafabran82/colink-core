import json
from xrpl.wallet import Wallet

def main():
    # Create a new random wallet (testnet-compatible)
    wallet = Wallet.create()

    data = {
        "seed": wallet.seed,
        "address": wallet.classic_address,
    }

    print(json.dumps(data))

if __name__ == "__main__":
    main()
