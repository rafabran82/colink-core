import os, json, time
from decimal import Decimal, ROUND_UP
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import OfferCreate, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers, Ledger

load_dotenv(".env.testnet")

RPC        = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER     = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_ADDR   = os.getenv("XRPL_HOT_ADDRESS")
CODE       = os.getenv("COPX_CODE","COPX")

BUY_QTY    = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIPPAGE   = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))
CUSHION    = int(os.getenv("CAP_CUSHION_DROPS","20"))

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)

client = JsonRpcClient(RPC)

def acct_info(addr:str):
    return client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result["account_data"]

def spendable_drops(addr:str)->int:
    i = acct_info(addr)
    balance = int(i["Balance"])
    oc = int(i.get("OwnerCount",0))
    led = client.request(Ledger(ledger_index="validated", full=False, accounts=False, expand=False, owner_funds=False, transactions=False)).result
    rbase = int(led.get("ledger",{}).get("reserve_base","10000000"))
    rinc  = int(led.get("ledger",{}).get("reserve_inc","2000000"))
    spend = max(0, balance - (rbase + oc*rinc))
    print(f"Spendable drops: {spend} (balance={balance}, owner_count={oc}, reserve_base={rbase}, reserve_inc={rinc})")
    return spend

def have_trustline(holder:str)->bool:
    lines = client.request(AccountLines(account=holder, ledger_index="validated")).result.get("lines",[])
    for ln in lines:
        if ln.get("currency")==CUR and ln.get("account")==ISSUER:
            return True
    return False

def ensure_trustline(addr:str, seed:str, limit="20000"):
    if have_trustline(addr):
        print("TrustSet result: already")
        return
    w = Wallet.from_seed(seed)
    ts = TrustSet(account=addr, limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=limit))
    txr = submit_and_wait(sign(autofill(ts, client), w), client).result
    print("TrustSet result:", txr.get("engine_result"))
    for _ in range(6):
        if have_trustline(addr):
            break
        time.sleep(1.2)

def book_top_ask(taker_addr:str):
    # maker pays COPX, gets XRP; price quoted from taker's perspective
    res = client.request(BookOffers(
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR, "issuer":ISSUER},
        taker=taker_addr,                    # <- important so self/unfunded rules/fees apply
        ledger_index="validated",
        limit=20
    )).result
    offers = res.get("offers",[])
    norm = []
    for o in offers:
        # skip self-owned (self-cross forbidden)
        if o.get("Account") == taker_addr:
            continue
        tg = o.get("taker_gets")
        tp = o.get("taker_pays")
        if isinstance(tg, str):
            drops = int(tg)
        elif isinstance(tg, dict):
            from decimal import Decimal as D
            drops = int(D(str(tg.get("value","0"))) * D(1_000_000))
        else:
            continue
        if not isinstance(tp, dict):
            continue
        from decimal import Decimal as D
        copx = D(str(tp.get("value","0")))
        if copx <= 0:
            continue
        px = Decimal(drops) / Decimal(1_000_000) / copx
        norm.append({"owner": o.get("Account"), "drops": drops, "copx": copx, "px": px})
    norm.sort(key=lambda x: x["px"])
    return norm[0] if norm else None

def ceil_drops(xrp:Decimal)->int:
    return int((xrp * Decimal(1_000_000)).to_integral_value(rounding=ROUND_UP))

def main():
    seed = os.getenv("XRPL_TAKER_SEED")
    addr = os.getenv("XRPL_TAKER_ADDRESS")
    if not seed or not addr:
        raise SystemExit("Set XRPL_TAKER_ADDRESS and XRPL_TAKER_SEED (must differ from HOT).")

    if addr == HOT_ADDR:
        raise SystemExit("Taker must NOT equal HOT (self-cross is forbidden). Use a separate taker account.")

    print("Taker:", addr)
    ensure_trustline(addr, seed)
    spendable = spendable_drops(addr)

    top = book_top_ask(addr)
    if not top:
        raise SystemExit("No executable asks from your perspective (likely only self-owned asks present).")
    print(f"Top ask ~ {top['px']:.6f} XRP/COPX | size≈{top['copx']} COPX | owner={top['owner']}")

    cap_px   = top["px"] * (Decimal(1) + SLIPPAGE)
    cap_xrp  = BUY_QTY * cap_px
    cap_drop = ceil_drops(cap_xrp) + CUSHION
    print(f"Paying up to {cap_px:.6f} for {BUY_QTY} -> cap {cap_xrp:.6f} XRP ({cap_drop} drops incl. cushion {CUSHION})")

    if cap_drop > spendable:
        raise SystemExit(f"Cap {cap_drop} drops exceeds spendable {spendable} drops.")

    taker = Wallet.from_seed(seed)
    tx = OfferCreate(
        account=addr,
        flags=0x00020000,  # tfImmediateOrCancel
        taker_gets=str(cap_drop),
        taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(BUY_QTY)),
    )
    stx = sign(autofill(tx, client), taker)
    res = submit_and_wait(stx, client).result
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
