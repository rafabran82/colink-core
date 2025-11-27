import sys
import json
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import BookOffers
from xrpl.models.currencies import IssuedCurrency

# Get arguments passed from PowerShell
base_currency = sys.argv[1]
base_issuer   = sys.argv[2]
counter       = sys.argv[3]
rpc           = sys.argv[4]

# Create the USD currency object
usd_currency = IssuedCurrency(currency="USD", issuer=base_issuer)

# Initialize the client
client = JsonRpcClient(rpc)

# Create the request
request = BookOffers(
    taker_gets={'currency': base_currency, 'issuer': base_issuer},
    taker_pays=usd_currency
)

# Make the request and print the result
response = client.request(request)
print(json.dumps(response.result, indent=2))
