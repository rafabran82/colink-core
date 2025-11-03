import os, json, time, requests
from decimal import Decimal, ROUND_UP
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, BookOffers

load_dotenv(".env.testnet")
RPC     = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
CODE    = os.getenv("COPX_CODE","COPX")
BUY_QTY = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIP    = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))
CUSH_D  = int(os.getenv("CAP_CUSHION_DROPS","20"))

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

def _get(obj, *names):
    for n in names:
        if n in obj: return obj[n]
    return None

def _drops_from_amount(x):
    if isinstance(x, str):
        return int(x)
    if isinstance(x, dict):
        if x.get("currency")=="XRP" and "value" in x:
            return int(Decimal(str(x["value"])) * Decimal(1_000_000))
    return None

def _iou_value(x):
    if isinstance(x, dict) and "value" in x:
        return Decimal(str(x["value"]))
    return None

def top_ask():
    r = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR, "issuer":ISSUER},
        ledger_index="validated",
        limit=10
    )).result
    for o in r.get("offers", []):
        tg = _get(o, "taker_gets","TakerGets")
        tp = _get(o, "taker_pays","TakerPays")
        drops = _drops_from_amount(tg)
        copx  = _iou_value(tp)
        if drops is None or copx is None or copx == 0:
            continue
        px = (Decimal(drops)/Decimal(1_000_000)) / copx  # XRP per COPX
        return px, copx
    return None

def round_drops(xrp:Decimal)->int:
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

    ts = TrustSet(account=addr, limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000"))
    tsr = submit_tx(ts, taker)
    print("TrustSet result:", tsr.get("engine_result"))

    top = top_ask()
    if not top:
        print("No well-formed asks on book; aborting.")
        return
    px, size = top
    eff_px = px * (Decimal(1)+SLIP)
    cap_xrp = BUY_QTY * eff_px
    cap_drops = round_drops(cap_xrp)
    print(f"Top ask ~ {px:.6f} XRP/COPX; paying up to {eff_px:.6f} for {BUY_QTY} -> cap {cap_xrp:.6f} XRP ({cap_drops} drops)")

    tx = OfferCreate(
        account = addr,
        taker_gets = str(cap_drops),  # XRP drops
        taker_pays = IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(BUY_QTY)),
        flags = 0x00020000  # tfImmediateOrCancel
    )
    res = submit_tx(tx, taker)
    print("IOC result:", json.dumps(res, indent=2))
    if res.get("engine_result") == "tecKILLED":
        print("Note: tecKILLED = no match at/under your cap in the same ledger. Try a slightly higher slippage/cap and retry.")
if __name__ == "__main__":
    main()
