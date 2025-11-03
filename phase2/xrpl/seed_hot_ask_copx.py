import os
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC      = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
client   = JsonRpcClient(RPC)
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED = os.getenv("XRPL_HOT_SEED")
HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE     = os.getenv("COPX_CODE","COPX")

# change these two to taste
AMOUNT_COPX = Decimal(os.getenv("SEED_ASK_AMOUNT_COPX", "1000"))     # how many COPX to sell
PRICE_XRP_PER_COPX = Decimal(os.getenv("SEED_ASK_PRICE_XRP", "0.00025"))

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)
hot = Wallet.from_seed(HOT_SEED)

# Maker ASK: receive XRP, pay COPX
taker_pays_issued = IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(AMOUNT_COPX))
xrp_total = AMOUNT_COPX * PRICE_XRP_PER_COPX
taker_gets_drops = xrp_to_drops(xrp_total)

ask = OfferCreate(
    account=HOT_ADDR,
    taker_gets=taker_gets_drops,           # we (maker) GET XRP
    taker_pays=taker_pays_issued,          # we PAY COPX
    flags=0
)

stx = sign(autofill(ask, client), hot)
res = submit_and_wait(stx, client)
print(res.result.get("engine_result"), res.result.get("hash"))
