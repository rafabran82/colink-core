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
MAKER    = os.getenv("XRPL_MAKER_ADDRESS")
MSEED    = os.getenv("XRPL_MAKER_SEED")

ASK_QTY  = Decimal(os.getenv("ASK_QTY_COPX","500"))   # size of ask (COPX)
ASK_PX   = Decimal(os.getenv("ASK_PRICE_XRP","0.004"))# XRP per COPX

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

def drops(x: Decimal)->int:
    return int((x*Decimal(1_000_000)).to_integral_value())

def main():
    if not all([ISSUER, MAKER, MSEED]):
        print("Missing ISSUER/MAKER/MSEED")
        return
    CODE160 = to160(CODE_ASC)
    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(MSEED)

    # Maker sells ASK_QTY COPX, receives XRP = ASK_QTY * ASK_PX
    taker_pays_ic   = IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(ASK_QTY))  # what taker pays (COPX)
    taker_gets_xrp  = drops(ASK_QTY * ASK_PX)                                                    # what taker gets (XRP drops)

    tx = OfferCreate(
        account=MAKER,
        taker_gets=str(taker_gets_xrp),     # maker receives XRP (drops)
        taker_pays=taker_pays_ic,           # maker sells COPX
        flags=0
    )
    stx = sign(autofill(tx, c), w)
    res = submit_and_wait(stx, c).result
    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "ask_qty_copx": str(ASK_QTY),
        "ask_px_xrp": str(ASK_PX)
    }, indent=2))

if __name__ == "__main__":
    main()
