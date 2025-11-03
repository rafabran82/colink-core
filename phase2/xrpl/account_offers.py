import os, json, time
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountOffers

load_dotenv(".env.testnet")
RPC = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(RPC)

acct = os.getenv("XRPL_HOT_ADDRESS")
res = client.request(AccountOffers(account=acct)).result
print("Account:", acct)
print("Offers count:", len(res.get("offers", [])))
print(json.dumps(res.get("offers", []), indent=2))
