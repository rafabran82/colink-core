import os, time, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import BookOffers

load_dotenv(".env.testnet")
RPC     = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED= os.getenv("XRPL_HOT_SEED")
HOT_ADDR= os.getenv("XRPL_HOT_ADDRESS")
CODE    = os.getenv("COPX_CODE","COPX")
PX_XRP  = Decimal(os.getenv("SEED_ASK_PRICE_XRP","0.004"))
QTY     = Decimal(os.getenv("SEED_ASK_QTY_COPX","1000"))

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)

client = JsonRpcClient(RPC)
hot = Wallet.from_seed(HOT_SEED)

taker_gets_drops = int((PX_XRP * QTY * Decimal(1_000_000)).to_integral_value())  # maker gets XRP
tx = OfferCreate(
    account=HOT_ADDR,
    taker_gets=str(taker_gets_drops),  # XRP as drops string
    taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(QTY)),
    flags=0
)
stx = sign(autofill(tx, client), hot)
res = submit_and_wait(stx, client).result
print(json.dumps(res, indent=2))

# give one or two ledgers
time.sleep(4)
book = client.request(BookOffers(
    taker_gets={"currency":"XRP"},
    taker_pays={"currency":CUR, "issuer":ISSUER},
    ledger_index="validated",
    limit=5
)).result
print("\nAfter seed, top-of-book:")
print(json.dumps(book.get("offers",[])[:3], indent=2))
