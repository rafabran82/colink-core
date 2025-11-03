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
    if len(b)>20: raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)
hot = Wallet.from_seed(HOT_SEED)

# Hot places a BUY (bid): gives XRP, receives COPX
bid = OfferCreate(
    account=HOT_ADDR,
    taker_gets=xrp_to_drops(Decimal("0.25")),  # pay 0.25 XRP
    taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="1000"),  # receive 1000 COPX
    flags=0
)
bid = sign(autofill(bid, client), hot)
res = submit_and_wait(bid, client)
print(json.dumps(res.result, indent=2))
