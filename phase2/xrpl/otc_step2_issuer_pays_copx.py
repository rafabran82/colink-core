import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
ISSUER_SD= os.getenv("XRPL_ISSUER_SEED")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
CODE_ASC = os.getenv("COPX_CODE","COPX")
QTY      = Decimal(os.getenv("OTC_COPX_QTY","0"))

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

def main():
    if not (ISSUER and ISSUER_SD and TAKER and QTY>0):
        print(json.dumps({"error":"missing env XRPL_ISSUER_*, XRPL_TAKER_ADDRESS or OTC_COPX_QTY"}, indent=2))
        return

    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(ISSUER_SD)
    amt = IssuedCurrencyAmount(currency=to160(CODE_ASC), issuer=ISSUER, value=str(QTY))
    pay = Payment(account=ISSUER, destination=TAKER, amount=amt)
    stx = sign(autofill(pay, c), w)
    res = submit_and_wait(stx, c).result

    out = {
        "engine_result": res.get("engine_result"),
        "validated": res.get("validated", False),
        "ledger_index": res.get("ledger_index"),
        "hash": (res.get("tx_json") or {}).get("hash"),
        "issuer_sent": str(QTY)
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
