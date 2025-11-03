import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC      = "https://s.altnet.rippletest.net:51234"
client   = JsonRpcClient(RPC)
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED = os.getenv("XRPL_HOT_SEED")
HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE     = os.getenv("COPX_CODE","COPX")

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)
hot = Wallet.from_seed(HOT_SEED)

# Offer #1: sell 5,000 COPX for 1.25 XRP (price = 0.00025 XRP/COPX)
o1 = OfferCreate(
    account=HOT_ADDR,
    taker_gets=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="5000"),
    taker_pays=xrp_to_drops(Decimal("1.25")),
    flags=0,
)
o1 = sign(autofill(o1, client), hot)
r1 = submit_and_wait(o1, client)

# Offer #2: sell 1,000 COPX for 0.25 XRP (same price, smaller size)
o2 = OfferCreate(
    account=HOT_ADDR,
    taker_gets=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="1000"),
    taker_pays=xrp_to_drops(Decimal("0.25")),
    flags=0,
)
o2 = sign(autofill(o2, client), hot)
r2 = submit_and_wait(o2, client)

print("Seed results:")
print(json.dumps({"o1": r1.result, "o2": r2.result}, indent=2))
