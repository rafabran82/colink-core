import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import BookOffers
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
CODE_ASC = os.getenv("COPX_CODE","COPX")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
TAKER_SD = os.getenv("XRPL_TAKER_SEED")

BUY_QTY  = Decimal(os.getenv("MBUY_QTY_COPX", "250"))
SLIP     = Decimal(os.getenv("MBUY_SLIPPAGE","0.02"))
CUSHION  = int(os.getenv("MBUY_CUSHION_DROPS","20"))

TF_IMMEDIATE_OR_CANCEL = 0x00020000

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CODE160 = to160(CODE_ASC)

def drops(x):
    return int((Decimal(str(x))*Decimal(1_000_000)).to_integral_value())

def best_px(client: JsonRpcClient):
    res = client.request(BookOffers(
        taker=TAKER,
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CODE160,"issuer":ISSUER},
        ledger_index="validated",
        limit=10
    )).result
    offers = res.get("offers",[]) or []
    best=None
    from decimal import Decimal as D
    for o in offers:
        tp=o.get("taker_pays") or o.get("TakerPays")
        tg=o.get("taker_gets") or o.get("TakerGets")
        if not isinstance(tp,dict): continue
        size=D(str(tp.get("value","0")))
        if size<=0: continue
        if isinstance(tg,str) and tg.isdigit():
            dr=int(tg)
        elif isinstance(tg,dict) and (tg.get("currency","").upper()=="XRP"):
            dr=drops(tg["value"])
        else:
            continue
        px=(D(dr)/D(1_000_000))/size
        if best is None or px<best: best=px
    return best

def main():
    if not (TAKER and TAKER_SD and ISSUER):
        print("Missing env XRPL_TAKER_* or ISSUER.")
        return

    client = JsonRpcClient(RPC)
    w = Wallet.from_seed(TAKER_SD)

    px = best_px(client)
    if px is None:
        print("No asks visible.")
        return

    worst = px*(Decimal(1)+SLIP)
    cap_drops = drops(BUY_QTY*worst) + CUSHION

    # Market buy via OfferCreate(IOC):
    # You PAY up to cap_drops in XRP (TakerPays), and you RECEIVE BUY_QTY COPX (TakerGets).
    tx = OfferCreate(
        account=TAKER,
        taker_pays=str(cap_drops),  # XRP (drops) you are willing to spend
        taker_gets=IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(BUY_QTY)),
        flags=TF_IMMEDIATE_OR_CANCEL
    )
    stx = sign(autofill(tx, client), w)
    res = submit_and_wait(stx, client).result

    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "buy_qty_copx": str(BUY_QTY),
        "best_px_est": f"{px:.6f}",
        "cap_drops": cap_drops
    }, indent=2))

if __name__ == "__main__":
    main()
