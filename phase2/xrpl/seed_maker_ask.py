import os, json, time
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
MAKER   = os.getenv("XRPL_MAKER_ADDRESS")
MSEED   = os.getenv("XRPL_MAKER_SEED")
CODE    = os.getenv("COPX_CODE","COPX")
PX_XRP  = Decimal(os.getenv("SEED_ASK_PRICE_XRP","0.004"))   # XRP per 1 COPX
QTY     = Decimal(os.getenv("SEED_ASK_QTY_COPX","1000"))     # COPX to sell

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)
client = JsonRpcClient(RPC)
mw = Wallet.from_seed(MSEED)

# Maker sells COPX, receives XRP
taker_gets_drops = int((PX_XRP * QTY * Decimal(1_000_000)).to_integral_value())  # XRP in drops

tx = OfferCreate(
    account=MAKER,
    taker_gets=str(taker_gets_drops),  # maker receives XRP (drops)
    taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(QTY)),  # maker sells COPX
    flags=0
)

res = submit_and_wait(sign(autofill(tx, client), mw), client).result
print(json.dumps({"engine_result": res.get("engine_result"), "tx_hash": res.get("tx_json",{}).get("hash")}, indent=2))

# small pause for validation
time.sleep(3)

# Snapshot book from MAKER's perspective (optional)
book = client.request(BookOffers(
    taker=getattr(mw, "classic_address", getattr(mw, "address", None)),
    taker_gets={"currency":"XRP"},
    taker_pays={"currency":CUR, "issuer":ISSUER},
    ledger_index="validated",
    limit=5
)).result

print("\nTop-of-book snapshot (first 3):")
print(json.dumps(book.get("offers",[])[:3], indent=2))
