import os, json
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC       = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER    = os.getenv("XRPL_ISSUER_ADDRESS")
ISSUER_SD = os.getenv("XRPL_ISSUER_SEED")
TAKER     = os.getenv("XRPL_TAKER_ADDRESS")
CODE_ASC  = os.getenv("COPX_CODE","COPX")
QTY       = os.getenv("OTC_COPX_QTY","250")

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

def main():
    if not all([ISSUER, ISSUER_SD, TAKER]):
        print("Missing envs: ISSUER/ISSUER_SD/TAKER"); return
    code160 = to160(CODE_ASC)
    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(ISSUER_SD)

    amt = IssuedCurrencyAmount(currency=code160, issuer=ISSUER, value=str(QTY))
    tx  = Payment(account=ISSUER, destination=TAKER, amount=amt)
    stx = sign(autofill(tx, c), w)
    res = submit_and_wait(stx, c).result
    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "hash": res.get("tx_json",{}).get("hash"),
        "issuer_sent": str(QTY)
    }, indent=2))

if __name__ == "__main__":
    main()
