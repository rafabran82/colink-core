from config import settings
print("XRPL_RPC_URL:", settings.XRPL_RPC_URL)
print("ISSUER_ADDRESS:", settings.ISSUER_ADDRESS)
print("TRADER_ADDRESS:", settings.TRADER_ADDRESS)
print("ISSUER_SEED:", "SET" if settings.ISSUER_SEED else "MISSING")
print("TRADER_SEED:", "SET" if settings.TRADER_SEED else "MISSING")
