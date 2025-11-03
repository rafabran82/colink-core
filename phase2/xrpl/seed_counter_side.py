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
RPC     = "https://s.altnet.rippletest.net:51234"
client  = JsonRpcClient(RPC)
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED= os.getenv("XRPL_HOT_SEED")
HOT_ADDR= os.getenv("XRPL_HOT_ADDRESS")
CODE    = os.getenv("COPX_CODE","COPX")

def to160(c:str)->str:
    if len(c)<=3: return c
    b=c.encode("ascii")
    if len(b)>20: raise ValueError("code>20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)
hot = Wallet.from_seed(HOT_SEED)

# Offer A: give 10,000 COPX, receive up to 2 XRP (price ~0.0002 XRP/COPX)
offer_a = OfferCreate(
    account=HOT_ADDR,
    taker_gets=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="10000"),
    taker_pays=xrp_to_drops(Decimal("2")),  # in drops
    flags=0 # resting offer (not IOC), so taker can hit it
)
offer_a = sign(autofill(offer_a, client), hot)
ra = submit_and_wait(offer_a, client)
print("Offer A:", json.dumps(ra.result, indent=2))

# Offer B: give 1,000 COPX for 0.25 XRP to ensure a small match
offer_b = OfferCreate(
    account=HOT_ADDR,
    taker_gets=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="1000"),
    taker_pays=xrp_to_drops(Decimal("0.25")),
    flags=0
)
offer_b = sign(autofill(offer_b, client), hot)
rb = submit_and_wait(offer_b, client)
print("Offer B:", json.dumps(rb.result, indent=2))
