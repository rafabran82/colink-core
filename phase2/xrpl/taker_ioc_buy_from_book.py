import os, json, time
from decimal import Decimal, ROUND_UP
from dotenv import load_dotenv

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import OfferCreate, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import (
    AccountInfo,
    AccountLines,
    BookOffers,
    Ledger
)

load_dotenv(".env.testnet")

RPC        = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER     = os.getenv("XRPL_ISSUER_ADDRESS")
CODE       = os.getenv("COPX_CODE","COPX")

BUY_QTY    = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIPPAGE   = Decimal(os.getenv("TAKER_SLIPPAGE","0.02")) # 2%
CUSHION    = int(os.getenv("CAP_CUSHION_DROPS","20"))

def to160(code:str)->str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)

client = JsonRpcClient(RPC)

def acct_info(addr:str):
    return client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result["account_data"]

def spendable_drops(addr:str)->int:
    i = acct_info(addr)
    balance = int(i["Balance"])
    owner_count = int(i.get("OwnerCount",0))
    # Testnet reserves (typical): base 10 XRP, incremental 2 XRP per object. Convert to drops.
    # We fetch from ledger to be robust.
    led = client.request(Ledger(ledger_index="validated", full=False, accounts=False, expand=False, owner_funds=False, transactions=False)).result
    rbase_drops = int(led.get("ledger",{}).get("reserve_base","10000000"))   # default 10 XRP
    rinc_drops  = int(led.get("ledger",{}).get("reserve_inc","2000000"))     # default 2 XRP
    reserve = rbase_drops + owner_count * rinc_drops
    spendable = max(0, balance - reserve)
    print(f"Spendable drops: {spendable} (balance={balance}, owner_count={owner_count}, reserve_base={rbase_drops}, reserve_inc={rinc_drops})")
    return spendable

def have_trustline(holder:str)->bool:
    lines = client.request(AccountLines(account=holder, ledger_index="validated")).result.get("lines",[])
    for ln in lines:
        if ln.get("currency")==CUR and ln.get("account")==ISSUER:
            return True
    return False

def ensure_trustline(holder_addr:str, holder_seed:str, limit:str="20000"):
    if have_trustline(holder_addr):
        print("TrustSet result: already")
        return
    w = Wallet.from_seed(holder_seed)
    ts = TrustSet(
        account=holder_addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=limit)
    )
    txr = submit_and_wait(sign(autofill(ts, client), w), client).result
    print("TrustSet result:", txr.get("engine_result"))
    # wait until validated view shows it
    for _ in range(6):
        if have_trustline(holder_addr):
            break
        time.sleep(1.2)

def book_top_ask():
    # maker pays COPX (IOU), gets XRP (drops)
    res = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR, "issuer":ISSUER},
        ledger_index="validated",
        limit=10
    )).result
    offers = res.get("offers",[])
    norm = []
    for o in offers:
        tg = o.get("taker_gets")
        tp = o.get("taker_pays")
        if isinstance(tg, str):
            drops = int(tg)
        elif isinstance(tg, dict):
            drops = int(Decimal(str(tg.get("value","0"))) * Decimal(1_000_000))
        else:
            continue
        if isinstance(tp, dict):
            copx = Decimal(str(tp.get("value","0")))
        else:
            # malformed for this book side; skip
            continue
        if copx <= 0: 
            continue
        px = Decimal(drops) / Decimal(1_000_000) / copx  # XRP per COPX
        norm.append({"owner": o.get("Account"), "drops": drops, "copx": copx, "px": px})
    norm.sort(key=lambda x: x["px"])  # cheapest ask first
    return norm[0] if norm else None

def ceil_drops(xrp:Decimal)->int:
    # round up to whole drops
    return int((xrp * Decimal(1_000_000)).to_integral_value(rounding=ROUND_UP))

def main():
    seed = os.getenv("XRPL_TAKER_SEED") or os.getenv("XRPL_HOT_SEED")  # allow hot as taker in test
    addr = os.getenv("XRPL_TAKER_ADDRESS") or os.getenv("XRPL_HOT_ADDRESS")
    if not seed or not addr:
        raise SystemExit("XRPL_TAKER_{SEED,ADDRESS} (or HOT equivalents) are required.")

    print("Taker:", addr)

    # 1) Ensure taker trustline EXISTS (critical for buy offers receiving COPX)
    ensure_trustline(addr, seed)

    # 2) Compute spendable XRP to avoid reserve violations
    spendable = spendable_drops(addr)

    # 3) Snapshot top ask
    top = book_top_ask()
    if not top:
        raise SystemExit("No asks available in the book.")
    best_px = top["px"]
    print(f"Top ask ~ {best_px:.6f} XRP/COPX")

    cap_px = best_px * (Decimal(1) + SLIPPAGE)
    cap_xrp = (BUY_QTY * cap_px)
    cap_drops = ceil_drops(cap_xrp) + CUSHION

    print(f"Paying up to {cap_px:.6f} for {BUY_QTY} -> cap {cap_xrp:.6f} XRP ({cap_drops} drops incl. cushion {CUSHION})")

    if cap_drops > spendable:
        raise SystemExit(f"Cap {cap_drops} drops exceeds spendable {spendable} drops. Reduce BUY_QTY or top up XRP.")

    # 4) Build IOC buy: pay XRP (TakerGets = XRP) up to cap, receive COPX qty
    taker = Wallet.from_seed(seed)
    tx = OfferCreate(
        account=addr,
        # tfImmediateOrCancel
        flags=0x00020000,
        taker_gets=str(cap_drops),  # max XRP you’re willing to pay (cap)
        taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(BUY_QTY)),
    )
    stx = sign(autofill(tx, client), taker)
    res = submit_and_wait(stx, client).result
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
