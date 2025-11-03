import os, json, time
from decimal import Decimal, ROUND_UP
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, BookOffers
import requests

load_dotenv(".env.testnet")
RPC     = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
CODE    = os.getenv("COPX_CODE","COPX")
BUY_QTY = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIP    = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))   # 2% default
CUSH_D  = int(os.getenv("CAP_CUSHION_DROPS","20"))      # drop cushion

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)
client = JsonRpcClient(RPC)

def faucet_new():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={})
    r.raise_for_status()
    p = r.json()
    seed = p.get("seed")
    addr = (p.get("account") or {}).get("classicAddress") or (p.get("account") or {}).get("address")
    if not seed or not addr:
        raise RuntimeError("Faucet payload missing seed/address")
    time.sleep(1.2)
    return addr, seed

def wait_seq(addr, timeout=10):
    t0=time.time()
    while time.time()-t0<timeout:
        ai = client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result
        if ai and "account_data" in ai: return ai["account_data"]
        time.sleep(0.8)
    raise TimeoutError("AccountInfo not ready")

def top_ask():
    r = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR, "issuer":ISSUER},
        ledger_index="validated",
        limit=5
    )).result
    offers = r.get("offers", [])
    if not offers: return None
    o = offers[0]
    drops = int(o["taker_gets"]) if isinstance(o["taker_gets"], str) else int(o["taker_gets"]["value"])
    copx  = Decimal(str(o["taker_pays"]["value"]))
    px = (Decimal(drops)/Decimal(1_000_000)) / copx  # XRP per COPX
    return px, o

def round_drops(xrp:Decimal)->int:
    # round UP to whole drops, add small cushion
    drops = int((xrp*Decimal(1_000_000)).to_integral_value(rounding=ROUND_UP))
    return drops + CUSH_D

def submit_tx(tx, w):
    stx = sign(autofill(tx, client), w)
    return submit_and_wait(stx, client).result

def main():
    addr, seed = faucet_new()
    print("Taker:", addr)
    taker = Wallet.from_seed(seed)
    wait_seq(addr)

    # open trustline
    ts = TrustSet(account=addr, limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000"))
    tsr = submit_tx(ts, taker)
    print("TrustSet result:", tsr.get("engine_result"))

    # check book
    ask = top_ask()
    if not ask:
        print("No asks on book; aborting.")
        return
    px, row = ask
    eff_px = px * (Decimal(1) + SLIP)
    cap_xrp = BUY_QTY * eff_px
    cap_drops = round_drops(cap_xrp)

    print(f"Top ask ~ {px:.6f} XRP/COPX; paying up to {eff_px:.6f} for {BUY_QTY} -> cap {cap_xrp:.6f} XRP ({cap_drops} drops)")

    # IOC: we WANT COPX, so we pay XRP (TakerGets = XRP), receive COPX (TakerPays = IOU)
    tx = OfferCreate(
        account = addr,
        taker_gets = str(cap_drops),  # XRP in drops as string
        taker_pays = IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(BUY_QTY)),
        flags = 0x00020000  # tfImmediateOrCancel
    )
    res = submit_tx(tx, taker)
    print("IOC result:", json.dumps(res, indent=2))

    # Quick note if killed
    if res.get("engine_result") == "tecKILLED":
        print("Note: tecKILLED means no match at/under your cap in the same ledger (no partial left). Try slightly higher slippage or re-snapshot the book.")
if __name__ == "__main__":
    main()
