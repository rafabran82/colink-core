from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import TrustSet
from xrpl.transaction import sign_and_submit
from xrpl.models.amounts import IssuedCurrencyAmount
import sys
import json

# -----------------------------------------------------
# ARGS
# -----------------------------------------------------
seed = sys.argv[1]              # family seed (sEd…)
issuer = sys.argv[2]            # classic issuer address (r…)
currency_hex = sys.argv[3]      # hex currency code

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# -----------------------------------------------------
# BUILD WALLET (correct for sEd seeds)
# -----------------------------------------------------
wallet = Wallet.from_seed(seed)

# -----------------------------------------------------
# BUILD TRUSTLINE
# -----------------------------------------------------
trustset_tx = TrustSet(
    account=wallet.classic_address,
    limit_amount=IssuedCurrencyAmount(
        currency=currency_hex,
        issuer=issuer,
        value="1000000000"
    )
)

# -----------------------------------------------------
# SIGN + SUBMIT
# -----------------------------------------------------
response = sign_and_submit(trustset_tx, client, wallet)

# -----------------------------------------------------
# OUTPUT
# -----------------------------------------------------
print("TX RESULT:")
try:
    print(json.dumps(response.to_dict(), indent=2))
except:
    print(response)
