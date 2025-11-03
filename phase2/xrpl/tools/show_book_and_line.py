import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountLines, BookOffers

load_dotenv(".env.testnet")
RPC     = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
CODE    = os.getenv("COPX_CODE","COPX")

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)

client = JsonRpcClient(RPC)

def _get(obj, *names):
    for n in names:
        if n in obj: return obj[n]
    return None

def _drops_from_amount(x):
    # XRP may be a string of drops OR dict {"currency":"XRP","value":"…"}
    if isinstance(x, str):
        return int(x)
    if isinstance(x, dict):
        cur = x.get("currency")
        if (cur == "XRP") and "value" in x:
            return int(Decimal(str(x["value"])) * Decimal(1_000_000))
    return None

def _iou_value(x):
    # IOU amount must be dict with "value"
    if isinstance(x, dict) and "value" in x:
        return Decimal(str(x["value"]))
    return None

def show_book():
    r = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR, "issuer":ISSUER},
        ledger_index="validated",
        limit=10
    )).result
    offers = r.get("offers", [])
    print(f"=== TOP ASK BOOK for {CODE} (maker pays {CODE}, gets XRP) ===")
    if not offers:
        print("(empty)")
        return None

    shown = 0
    for i,o in enumerate(offers,1):
        tg = _get(o, "taker_gets","TakerGets")
        tp = _get(o, "taker_pays","TakerPays")
        drops = _drops_from_amount(tg)
        copx  = _iou_value(tp)
        if drops is None or copx is None or copx == 0:
            continue
        px = (Decimal(drops)/Decimal(1_000_000)) / copx  # XRP/COPX
        acct = o.get("Account","?")
        print(f"{i:>2}. px≈{px:.6f} XRP/COPX  size={copx} COPX  owner={acct}")
        shown += 1
        if shown >= 10:
            break
    if shown == 0:
        print("(no well-formed rows)")
    return offers

def show_trustline(acct):
    res = client.request(AccountLines(account=acct, ledger_index="validated")).result
    print(f"\n=== TRUSTLINES for {acct} ===")
    any_line=False
    for ln in res.get("lines",[]):
        if ln["currency"]==CUR and ln["account"]==ISSUER:
            print(json.dumps(ln, indent=2)); any_line=True
    if not any_line:
        print("(no trustline to issuer yet)")

if __name__ == "__main__":
    acct = os.getenv("CHECK_ACCT","").strip()
    show_book()
    if acct:
        show_trustline(acct)
