import os, json, time, requests
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, BookOffers
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC     = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
client  = JsonRpcClient(RPC)
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
CODE    = os.getenv("COPX_CODE", "COPX")
STATE_PATH = os.path.join("phase2","state","taker.json")

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)

def faucet_new_account():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={})
    r.raise_for_status()
    p = r.json()
    seed = p.get("seed")
    classic = (p.get("account") or {}).get("classicAddress") or (p.get("account") or {}).get("address")
    if not seed or not classic:
        raise RuntimeError(f"Faucet payload missing seed/address:\n{json.dumps(p,indent=2)}")
    time.sleep(1.5)  # let account appear on-ledger
    return classic, seed

def wait_trustline(addr, currency_hex, issuer, timeout_s=20):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        res = client.request(AccountLines(account=addr, ledger_index="validated")).result
        for line in res.get("lines", []):
            if line["currency"] == currency_hex and line["account"] == issuer:
                return True
        time.sleep(1.0)
    return False

def book_has_hot_asks_at_or_better(price_xrp_per_copx: Decimal) -> bool:
    # BUY COPX (pay XRP) => we can hit asks where maker gets XRP and pays COPX.
    r = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency": CUR, "issuer": ISSUER}
    )).result
    for o in r.get("offers", [])[:12]:
        try:
            q = Decimal(str(o.get("quality")))
            if q <= price_xrp_per_copx:
                return True
        except Exception:
            pass
    return False

def save_state(addr, seed):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"address": addr, "seed": seed}, f, indent=2)

def submit_tx_and_wait(tx_obj, wallet):
    stx = sign(autofill(tx_obj, client), wallet)
    # Use library reliable submission (no manual polling / no tx.hash access needed)
    return submit_and_wait(stx, client).result

def main():
    taker_addr, taker_seed = faucet_new_account()
    print("Taker address:", taker_addr)
    save_state(taker_addr, taker_seed)
    taker = Wallet.from_seed(taker_seed)

    # 1) Trustline
    ts = TrustSet(
        account=taker_addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
    )
    tsr = submit_tx_and_wait(ts, taker)
    print("TrustSet tx:", json.dumps(tsr, indent=2))

    if not wait_trustline(taker_addr, CUR, ISSUER, timeout_s=20):
        raise SystemExit("Trustline not visible after wait—aborting BUY to avoid tecUNFUNDED_OFFER.")

    # 2) Ensure there is a sell at or below our price
    price = Decimal("0.00025")  # XRP per COPX
    if not book_has_hot_asks_at_or_better(price):
        raise SystemExit("No asks at or below 0.00025 XRP/COPX right now. Skipping IOC BUY.")

    # 3) Immediate-Or-Cancel BUY 1000 COPX for <= 0.25 XRP
    tfImmediateOrCancel = 0x00020000
    bid = OfferCreate(
        account=taker_addr,
        taker_gets=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="1000"),
        taker_pays=xrp_to_drops(Decimal("0.25")),
        flags=tfImmediateOrCancel
    )
    br = submit_tx_and_wait(bid, taker)
    print("IOC BUY result:", json.dumps(br, indent=2))

if __name__ == "__main__":
    main()
