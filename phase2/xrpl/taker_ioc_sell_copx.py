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
RPC    = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(RPC)
ISSUER = os.getenv("XRPL_ISSUER_ADDRESS")
CODE   = os.getenv("COPX_CODE","COPX")

STATE_PATH = os.path.join("phase2","state","taker.json")

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)

with open(STATE_PATH,"r",encoding="utf-8") as f:
    st = json.load(f)

TAKER_ADDR = st["address"]
TAKER_SEED = st["seed"]

taker = Wallet.from_seed(TAKER_SEED)

# IOC SELL: give 1000 COPX, receive up to 0.25 XRP at same price
tfImmediateOrCancel = 0x00020000
ask = OfferCreate(
    account=TAKER_ADDR,
    # For SELL: we give COPX and receive XRP.
    taker_gets=xrp_to_drops(Decimal("0.25")),  # we want XRP
    taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="1000"),  # we give COPX
    flags=tfImmediateOrCancel
)
ask = sign(autofill(ask, client), taker)
resp = submit_and_wait(ask, client)
print(json.dumps(resp.result, indent=2))
