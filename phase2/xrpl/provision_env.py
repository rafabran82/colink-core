from pathlib import Path
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet

env_path = Path(".") / ".env.testnet"
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# Create & fund two wallets (issuer + hot)
issuer = generate_faucet_wallet(client, debug=False)
hot    = generate_faucet_wallet(client, debug=False)

lines = [
    "XRPL_ENDPOINT=wss://s.altnet.rippletest.net:51233",
    f"XRPL_ISSUER_ADDRESS={issuer.classic_address}",
    f"XRPL_ISSUER_SEED={issuer.seed}",
    f"XRPL_HOT_ADDRESS={hot.classic_address}",
    f"XRPL_HOT_SEED={hot.seed}",
    "COPX_CODE=COPX",
    "ISSUANCE_AMOUNT=1000000",
    "SEED_LP_COPX=500000",
    "SEED_LP_COL=100000",
    "SEED_LP_XRP=2000",
    "DRY_RUN=true",
    ""
]
env_path.write_text("\r\n".join(lines), encoding="utf-8")

print("✅ Wrote .env.testnet")
print("Issuer:", issuer.classic_address, "Seed: ***" + issuer.seed[-4:])
print("Hot   :", hot.classic_address,    "Seed: ***" + hot.seed[-4:])
