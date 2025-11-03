import os, json
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountOffers
from xrpl.models.transactions import OfferCancel
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")
RPC     = "https://s.altnet.rippletest.net:51234"
client  = JsonRpcClient(RPC)
HOT_SEED= os.getenv("XRPL_HOT_SEED")
HOT_ADDR= os.getenv("XRPL_HOT_ADDRESS")
hot = Wallet.from_seed(HOT_SEED)

offers = client.request(AccountOffers(account=HOT_ADDR)).result.get("offers", [])
print(f"Found {len(offers)} offers to cancel.")
for o in offers:
    oc = OfferCancel(account=HOT_ADDR, offer_sequence=o["seq"])
    oc = sign(autofill(oc, client), hot)
    res = submit_and_wait(oc, client)
    print("Canceled", o["seq"], res.result.get("engine_result"))
