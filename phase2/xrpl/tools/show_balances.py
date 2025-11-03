import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines

load_dotenv(".env.testnet")
RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
CODE_ASC = os.getenv("COPX_CODE","COPX")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
MAKER    = os.getenv("XRPL_MAKER_ADDRESS")

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CODE160 = to160(CODE_ASC)

def xrp_balance(c, acct):
    r = c.request(AccountInfo(account=acct, ledger_index="validated")).result
    bal = int(r.get("account_data",{}).get("Balance","0"))
    return bal # drops

def ic_balance(c, holder, issuer, code160):
    r = c.request(AccountLines(account=holder, peer=issuer, ledger_index="validated")).result
    for ln in r.get("lines",[]):
        cur = (ln.get("currency") or "").upper()
        if cur in (CODE_ASC.upper(), CODE160.upper()) and ln.get("account")==issuer:
            try: return str(Decimal(str(ln.get("balance","0"))))
            except: return "0"
    return "0"

def main():
    c = JsonRpcClient(RPC)
    out = {
        "maker": {
            "xrp_drops": xrp_balance(c, MAKER),
            "copx": ic_balance(c, MAKER, ISSUER, CODE160),
        },
        "taker": {
            "xrp_drops": xrp_balance(c, TAKER),
            "copx": ic_balance(c, TAKER, ISSUER, CODE160),
        }
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
