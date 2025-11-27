import sys
import json
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import BookOffers
from xrpl.models.currencies import IssuedCurrency

# Fetch input parameters
base_currency = sys.argv[1]
base_issuer = sys.argv[2]
counter_currency = sys.argv[3]
rpc_url = sys.argv[4]

# Setup client and request
client = JsonRpcClient(rpc_url)

# Create the liquidity order
taker_gets = IssuedCurrency(currency=base_currency, issuer=base_issuer)
taker_pays = IssuedCurrency(currency=counter_currency, issuer=base_issuer)  # Adjust this if necessary

request = BookOffers(taker_gets=taker_gets, taker_pays=taker_pays)
response = client.request(request)

# Print the result
print(json.dumps(response.result, indent=2))
