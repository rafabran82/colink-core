import os, json
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines

load_dotenv(".env.testnet")
RPC = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(RPC)

# paste last taker address printed by the IOC script
TAKER = "rnXhog7CtNmUbSCqBQKPAnKwcP3VVLzJ9z"

ai = client.request(AccountInfo(account=TAKER, ledger_index="validated", strict=True)).result
print("XRP balance (drops):", ai["account_data"]["Balance"])

al = client.request(AccountLines(account=TAKER, ledger_index="validated")).result
print("Trust lines:")
print(json.dumps(al.get("lines", []), indent=2))
