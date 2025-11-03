import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
CODE_ASC = os.getenv("COPX_CODE","COPX")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
TAKER_SD = os.getenv("XRPL_TAKER_SEED")

# Params: "I want to BUY QTY COPX at price <= BID_PX_XRP per COPX"
QTY      = Decimal(os.getenv("BID_QTY_COPX", "250"))
BID_PX   = Decimal(os.getenv("BID_PRICE_XRP","0.004"))  # XRP / COPX
IOC      = bool(int(os.getenv("BID_USE_IOC","0")))       # 1 = tfImmediateOrCancel

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CODE160 = to160(CODE_ASC)

def drops(x):
    return int((Decimal(str(x))*Decimal(1_000_000)).to_integral_value())

def main():
    if not (TAKER and TAKER_SD and ISSUER):
        print("Missing env: XRPL_TAKER_ADDRESS/SEED and XRPL_ISSUER_ADDRESS")
        return

    client = JsonRpcClient(RPC)
    w = Wallet.from_seed(TAKER_SD)

    # Bid semantics on XRPL:
    #   You PAY XRP (TakerPays = drops), and you RECEIVE COPX (TakerGets = IssuedCurrencyAmount)
    pay_xrp = QTY * BID_PX
    taker_pays_drops = drops(pay_xrp)      # XRP you are willing to spend
    taker_gets_ic    = IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(QTY))

    flags = 0x00020000 if IOC else 0  # tfImmediateOrCancel if IOC requested

    tx = OfferCreate(
        account=TAKER,
        taker_pays=str(taker_pays_drops),   # XRP (drops)
        taker_gets=taker_gets_ic,           # COPX
        flags=flags
    )

    stx = sign(autofill(tx, client), w)
    res = submit_and_wait(stx, client).result
    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "bid_qty_copx": str(QTY),
        "bid_px_xrp": str(BID_PX),
        "taker_pays_drops": taker_pays_drops,
        "ioc": IOC
    }, indent=2))

if __name__ == "__main__":
    main()
