import os, json, time
from decimal import Decimal
from dotenv import load_dotenv
import requests

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, AccountLines

load_dotenv(".env.testnet")

RPC     = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
FAUCET  = os.getenv("XRPL_FAUCET_URL","https://faucet.altnet.rippletest.net/accounts")
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
ISEED   = os.getenv("XRPL_ISSUER_SEED")
CODE    = os.getenv("COPX_CODE","COPX")
FUND    = os.getenv("FUND_MAKER_COPX","5000")

def to160(code: str) -> str:
    if len(code) <= 3: return code
    b = code.encode("ascii")
    if len(b) > 20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40, "0")

CUR = to160(CODE)
client = JsonRpcClient(RPC)

def poll_account_funded(addr: str, timeout_s=30):
    """wait until account exists & has balance>0 on validated ledger"""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            res = client.request(AccountInfo(
                account=addr, ledger_index="validated", strict=True
            )).result
            bal = int(res.get("account_data",{}).get("Balance","0"))
            if bal > 0:
                return bal
        except Exception:
            pass
        time.sleep(1.2)
    return 0

def ensure_maker():
    maker = os.getenv("XRPL_MAKER_ADDRESS") or ""
    mseed = os.getenv("XRPL_MAKER_SEED") or ""
    if maker and mseed:
        return maker, mseed, False

    # create a fresh wallet and fund via HTTP faucet
    w = Wallet.create()
    try:
        r = requests.post(FAUCET, json={"destination": w.address}, timeout=20)
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Faucet funding failed: {e}")

    bal = poll_account_funded(w.address, timeout_s=45)
    if bal <= 0:
        raise RuntimeError("Faucet: account not funded after waiting")

    # persist in .env.testnet for future runs
    with open(".env.testnet", "a", encoding="utf-8") as f:
        f.write(f"\nXRPL_MAKER_ADDRESS={w.address}\nXRPL_MAKER_SEED={w.seed}\n")

    return w.address, w.seed, True

def main():
    if not (ISSUER and ISEED):
        raise SystemExit("Missing XRPL_ISSUER_ADDRESS / XRPL_ISSUER_SEED in .env.testnet")

    MAKER, MSEED, created = ensure_maker()
    iw = Wallet.from_seed(ISEED)
    mw = Wallet.from_seed(MSEED)

    # 1) Ensure MAKER trustline to ISSUER
    ts = TrustSet(
        account=MAKER,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000"),
        flags=0
    )
    tsr = submit_and_wait(sign(autofill(ts, client), mw), client).result

    # 2) Fund MAKER with COPX from ISSUER (direct issued-currency Payment)
    pay = Payment(
        account=ISSUER,
        destination=MAKER,
        amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(FUND))
    )
    pr = submit_and_wait(sign(autofill(pay, client), iw), client).result

    # 3) Verify via AccountLines (validated)
    al = client.request(AccountLines(account=MAKER, ledger_index="validated")).result
    bal = None
    for ln in al.get("lines", []):
        # AccountLines returns 3-letter code or 160-bit hex in 'currency'
        if ln.get("account") == ISSUER and ln.get("currency") in (CODE, CUR):
            bal = ln.get("balance"); break

    print(json.dumps({
        "maker_created": created,
        "maker": MAKER,
        "trustset_engine": tsr.get("engine_result"),
        "payment_engine": pr.get("engine_result"),
        "maker_copx_balance": bal,
        "funded_amount": FUND,
        "code": CODE
    }, indent=2))

if __name__ == "__main__":
    main()
