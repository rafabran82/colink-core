import os, json, time
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC     = "https://s.altnet.rippletest.net:51234"
client  = JsonRpcClient(RPC)
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
CODE    = os.getenv("COPX_CODE", "COPX")

def to160(code: str) -> str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("Currency code >20 bytes not allowed")
    return b.hex().upper().ljust(40, "0")

CUR = to160(CODE)

# 1) Create taker wallet (funded with ~1000 XRP on testnet)
taker = generate_faucet_wallet(client, debug=False)
print("Taker address:", taker.classic_address)

# 2) Trust COPX from issuer
trust = TrustSet(
    account=taker.classic_address,
    limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="1000000"),
)
trust = sign(autofill(trust, client), taker)
submit_and_wait(trust, client)
print("✅ Trustline opened.")

# 3) Place an IOC bid to BUY 10 COPX, paying up to 1 XRP
#    - TakerPays = XRP (drops) we're willing to spend (cap)
#    - TakerGets = 10 COPX we want to receive
taker_pays_drops = xrp_to_drops(Decimal("1"))  # spend cap
taker_gets_iou   = IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="10")

bid = OfferCreate(
    account=taker.classic_address,
    taker_pays=taker_pays_drops,   # XRP we're paying (in drops)
    taker_gets=taker_gets_iou,     # IOU we want to get
    # ImmediateOrCancel so nothing rests on book if not fully matchable
    flags=0x00020000,              # tfImmediateOrCancel
)

bid = sign(autofill(bid, client), taker)
resp = submit_and_wait(bid, client)
print("IOC bid result:", json.dumps(resp.result, indent=2))

print("Done. If not fully filled, increase spend cap or lower requested IOU amount.")
