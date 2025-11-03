import os, json, time, requests
from decimal import Decimal, ROUND_UP
from math import ceil
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, BookOffers
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC      = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
client   = JsonRpcClient(RPC)
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
CODE     = os.getenv("COPX_CODE", "COPX")
AMOUNT   = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "1000"))
SLIPPAGE = Decimal(os.getenv("TAKER_SLIPPAGE", "0.001"))
SLEEP_LEDGER = float(os.getenv("LEDGER_SLEEP", "3.0"))

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)

def faucet_new_account():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={})
    r.raise_for_status()
    p = r.json()
    seed = p.get("seed")
    classic = (p.get("account") or {}).get("classicAddress") or (p.get("account") or {}).get("address")
    if not seed or not classic:
        raise RuntimeError(f"Faucet payload missing seed/address:\n{json.dumps(p, indent=2)}")
    time.sleep(1.25)
    return classic, seed

def wait_trustline(addr, currency_hex, issuer, timeout_s=25):
    t0 = time.time()
    while time.time()-t0 < timeout_s:
        res = client.request(AccountLines(account=addr, ledger_index="validated")).result
        for line in res.get("lines", []):
            if line["currency"]==currency_hex and line["account"]==issuer:
                return True
        time.sleep(1.0)
    return False

def best_ask():
    r = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR,"issuer":ISSUER}
    )).result
    offers = r.get("offers", [])
    if not offers: return None
    return Decimal(str(offers[0]["quality"]))

def submit(tx, w, retries=2):
    last_err=None
    for i in range(retries+1):
        try:
            stx=sign(autofill(tx,client),w)
            res=submit_and_wait(stx,client).result
            return res
        except Exception as e:
            last_err=e
            time.sleep(SLEEP_LEDGER)
    raise last_err

def main():
    addr, seed = faucet_new_account()
    print("Taker:", addr)
    taker = Wallet.from_seed(seed)

    ts = TrustSet(account=addr, limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000"))
    tsr = submit(ts, taker)
    print("TrustSet:", tsr.get("engine_result"))
    if not wait_trustline(addr, CUR, ISSUER, 25):
        raise SystemExit("Trustline not found yet; stopping to avoid PATH/UNFUNDED issues.")

    q = best_ask()
    if q is None:
        print("No asks on book; nothing to take.")
        return

    px = (q*(Decimal(1)+SLIPPAGE)).quantize(Decimal("0.0000001"), rounding=ROUND_UP)
    xrp_cap = AMOUNT*px
    cap_drops = str(ceil((xrp_cap*Decimal(1_000_000))))
    print(f"Best ask ~ {q} XRP/COPX; paying up to {px} XRP/COPX for {AMOUNT} => cap {xrp_cap} XRP ({cap_drops} drops)")

    bid = OfferCreate(
        account=addr,
        taker_gets=cap_drops,  # XRP in drops (rounded UP)
        taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(AMOUNT)),
        flags=0x00020000
    )
    br = submit(bid, taker)
    print("IOC BUY result:", json.dumps(br, indent=2))

if __name__=="__main__":
    main()
