import os, json, time
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, AccountInfo

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER_A = os.getenv("XRPL_ISSUER_ADDRESS")
ISSUER_S = os.getenv("XRPL_ISSUER_SEED")
HOT_A    = os.getenv("XRPL_HOT_ADDRESS")
HOT_S    = os.getenv("XRPL_HOT_SEED")
CODE     = os.getenv("COPX_CODE","COPX")
AMT      = os.getenv("FUND_COPX_AMOUNT","5000")  # default fund 5k COPX

client = JsonRpcClient(RPC)

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)

def have_trustline(acct, cur, issuer):
    lines = client.request(AccountLines(account=acct, ledger_index="validated")).result.get("lines",[])
    for ln in lines:
        if ln.get("currency")==cur and ln.get("account")==issuer:
            return True
    return False

def trust_hot_if_needed():
    if have_trustline(HOT_A, CUR, ISSUER_A):
        return "already"
    hot = Wallet.from_seed(HOT_S)
    ts = TrustSet(
        account=HOT_A,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER_A, value="1000000000")
    )
    res = submit_and_wait(sign(autofill(ts, client), hot), client).result
    return res.get("engine_result")

def hot_balance():
    lines = client.request(AccountLines(account=HOT_A, ledger_index="validated")).result.get("lines",[])
    for ln in lines:
        if ln.get("currency")==CUR and ln.get("account")==ISSUER_A:
            return ln.get("balance","0")
    return "0"

def main():
    print(f"Issuing {AMT} {CODE} to HOT {HOT_A} from ISSUER {ISSUER_A}")
    st = trust_hot_if_needed()
    if st!="already":
        print("TrustSet (hot):", st)
        time.sleep(2)
    print("Hot pre-balance:", hot_balance())

    issuer = Wallet.from_seed(ISSUER_S)
    pay = Payment(
        account=ISSUER_A,
        destination=HOT_A,
        amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER_A, value=str(Decimal(AMT)))
    )
    res = submit_and_wait(sign(autofill(pay, client), issuer), client).result
    print("Issue tx:", json.dumps(res, indent=2))
    time.sleep(2)
    print("Hot post-balance:", hot_balance())

if __name__ == "__main__":
    main()
