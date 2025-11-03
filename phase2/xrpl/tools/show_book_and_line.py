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
    for i,o in enumerate(offers[:10],1):
        tg, tp = o.get("taker_gets"), o.get("taker_pays")
        drops = int(tg) if isinstance(tg,str) else int(tg.get("value","0"))
        copxv = Decimal(str(tp.get("value"))) if isinstance(tp,dict) else Decimal(0)
        px = (Decimal(drops)/Decimal(1_000_000)) / (copxv if copxv else Decimal(1))
        print(f"{i:>2}. px≈{px:.6f} XRP/COPX  size={copxv} COPX  owner={o.get('Account')}")
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
