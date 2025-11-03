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
CODE_ASC = os.getenv("COPX_CODE","COPX")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
MAKER    = os.getenv("XRPL_MAKER_ADDRESS")
MSEED    = os.getenv("XRPL_MAKER_SEED")

COPX_QTY = os.getenv("OTC_COPX_QTY","250")  # match your intended fill

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CODE160 = to160(CODE_ASC)

def main():
    if not all([ISSUER,MAKER,MSEED,TAKER]):
        print("Missing envs")
        return
    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(MSEED)

    amt = IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(COPX_QTY))
    pay = Payment(
        account=MAKER,
        destination=TAKER,
        amount=amt
    )
    stx = sign(autofill(pay, c), w)
    res = submit_and_wait(stx, c).result
    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "hash": res.get("tx_json",{}).get("hash"),
        "copx_sent": COPX_QTY
    }, indent=2))

if __name__ == "__main__":
    main()
