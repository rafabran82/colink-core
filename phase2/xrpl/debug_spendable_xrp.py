import os, json
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo

load_dotenv(".env.testnet")
RPC = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(RPC)

acct = input("Enter taker address: ").strip()
info = client.request(AccountInfo(account=acct, ledger_index="validated", strict=True)).result["account_data"]
bal = int(info["Balance"])  # drops
owner_count = int(info.get("OwnerCount", 0))

# Testnet defaults are typically Base=10 XRP, Increment=2 XRP (in drops below)
BASE = 10_000_000
INCR = 2_000_000
reserve = BASE + owner_count * INCR
spendable = max(0, bal - reserve)

print(json.dumps({
  "balance_drops": bal,
  "owner_count": owner_count,
  "assumed_base_reserve_drops": BASE,
  "assumed_inc_reserve_drops": INCR,
  "computed_reserve_drops": reserve,
  "spendable_drops": spendable,
  "spendable_xrp": spendable / 1_000_000
}, indent=2))
