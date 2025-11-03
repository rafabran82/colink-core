import os, json, re
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers, ServerState
from xrpl.models.transactions import OfferCreate, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
HOT      = os.getenv("XRPL_HOT_ADDRESS")
CODE_ASC = os.getenv("COPX_CODE","COPX")

TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
TAKER_SD = os.getenv("XRPL_TAKER_SEED")

BUY_QTY  = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIP     = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))
CUSHION  = int(os.getenv("CAP_CUSHION_DROPS","20"))

client = JsonRpcClient(RPC)

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CODE160 = to160(CODE_ASC)

def _drops_from_xrp(x): from decimal import Decimal as D; return int((D(str(x))*D(1_000_000)).to_integral_value())

def server_reserves_drops():
    st = client.request(ServerState()).result.get("state",{})
    vl = st.get("validated_ledger") or {}
    base = vl.get("reserve_base"); inc = vl.get("reserve_inc")
    base = int(base) if base is not None else 1_000_000
    inc  = int(inc)  if inc  is not None else   200_000
    return base, inc

def spendable_drops(acct:str):
    base, inc = server_reserves_drops()
    ai = client.request(AccountInfo(account=acct, ledger_index="validated")).result
    a  = ai.get("account_data",{})
    bal = int(a.get("Balance","0")); oc = int(a.get("OwnerCount",0))
    spendable = max(0, bal - (base + oc*inc))
    return spendable, bal, oc, base, inc

def maker_bal_copx(maker:str):
    res = client.request(AccountLines(account=maker, peer=ISSUER, ledger_index="validated", limit=400)).result
    for ln in res.get("lines",[]):
        cur = (ln.get("currency") or "").upper()
        if cur in (CODE_ASC.upper(), CODE160.upper()) and ln.get("account")==ISSUER:
            from decimal import Decimal as D
            try: return D(str(ln.get("balance","0")))
            except: return D(0)
    return Decimal(0)

def _get_case(o,*names):
    for n in names:
        if n in o: return o[n]
    return None

def normalize_offer(o):
    owner = o.get("Account")
    tp = _get_case(o,"taker_pays","TakerPays")     # maker sells COPX (dict)
    tg = _get_case(o,"taker_gets","TakerGets")     # maker receives XRP (drops or dict)
    if not owner or not isinstance(tp, dict): return None
    cur = (tp.get("currency") or "").upper()
    if cur not in (CODE_ASC.upper(), CODE160.upper()): return None
    from decimal import Decimal as D
    try: size_copx = D(str(tp.get("value","0")))
    except: return None
    if size_copx <= 0: return None
    if isinstance(tg,str):
        if not re.fullmatch(r"\d+", tg): return None
        drops = int(tg)
    elif isinstance(tg,dict):
        if (tg.get("currency","").upper()!="XRP") or (tg.get("value") is None): return None
        drops = _drops_from_xrp(tg["value"])
    else:
        return None
    if drops<=0: return None
    px = (D(drops)/D(1_000_000))/size_copx
    return {"owner":owner,"size_copx":size_copx,"drops":drops,"px":px}

def fetch_book(taker_view:str|None):
    req = BookOffers(
        taker=taker_view,
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CODE160,"issuer":ISSUER},
        ledger_index="validated",
        limit=50
    )
    res = client.request(req).result
    offers = res.get("offers",[]) or []
    out=[]
    for o in offers:
        no=normalize_offer(o)
        if no: out.append(no)
    return out

def ensure_trustline(acct:str, seed:str):
    try:
        ts = TrustSet(
            account=acct,
            limit_amount=IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(10_000_000))
        )
        w = Wallet.from_seed(seed)
        r = submit_and_wait(sign(autofill(ts, client), w), client).result
        print(f"TrustSet result: {r.get('engine_result') or 'already'}")
    except Exception:
        print("TrustSet result: already")

TF_IMMEDIATE_OR_CANCEL = 0x00020000  # valid for OfferCreate

def cap_drops_for(qty:Decimal, px:Decimal, slippage:Decimal, cushion:int)->int:
    from decimal import Decimal as D
    worst_px = px * (D(1)+slippage)
    cap_xrp  = qty * worst_px
    return int((cap_xrp*D(1_000_000)).to_integral_value(rounding="ROUND_CEILING")) + cushion

def ioc_slice_buy(acct:str, seed:str, qty:Decimal, cap_drops:int):
    # BUY COPX by offering to SELL up-to cap_drops XRP for qty COPX
    tx = OfferCreate(
        account=acct,
        taker_gets=str(cap_drops),  # you SELL XRP (drops)
        taker_pays=IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(qty)),  # you RECEIVE COPX
        flags=TF_IMMEDIATE_OR_CANCEL
    )
    stx = sign(autofill(tx, client), Wallet.from_seed(seed))
    return submit_and_wait(stx, client).result

def main():
    if not TAKER or not TAKER_SD:
        print("Set XRPL_TAKER_ADDRESS and XRPL_TAKER_SEED.")
        return
    if HOT and (TAKER==HOT):
        print("Taker must differ from HOT.")
        return

    print(f"Taker: {TAKER}")
    ensure_trustline(TAKER, TAKER_SD)

    spend, bal, oc, base, inc = spendable_drops(TAKER)
    print(f"Spendable drops: {spend} (balance={bal}, owner_count={oc}, reserve_base={base}, reserve_inc={inc})")

    book = fetch_book(TAKER) or fetch_book(None)
    candidates=[]
    for row in book:
        owner=row["owner"]
        if owner==TAKER or (HOT and owner==HOT): continue
        candidates.append({**row, "maker_bal": maker_bal_copx(owner)})
    candidates.sort(key=lambda r: r["px"])

    if not candidates:
        print("No executable asks from your perspective (none/self).")
        return

    print("\n[book_offers] candidates (up to 6):")
    for i,r in enumerate(candidates[:6],1):
        print(f" {i}. owner={r['owner']} px≈{r['px']:.6f} size={r['size_copx']} maker_bal={r['maker_bal']}")

    remaining = BUY_QTY
    attempts = []

    for row in candidates:
        if remaining <= 0: break
        from decimal import Decimal as D
        slice_qty = min(remaining, row["size_copx"], row["maker_bal"])
        if slice_qty <= 0: continue

        cap = cap_drops_for(slice_qty, row["px"], SLIP, CUSHION)
        if cap > spend:
            print(f"Skip owner={row['owner']} slice={slice_qty} — cap {cap} drops exceeds spendable {spend}.")
            continue

        print(f"\nSubmitting IOC slice: owner={row['owner']} qty={slice_qty} px≈{row['px']:.6f} cap={cap} drops …")
        try:
            res = ioc_slice_buy(TAKER, TAKER_SD, slice_qty, cap)
            er  = res.get("engine_result")
            attempts.append({"owner":row["owner"], "qty": str(slice_qty), "cap":cap, "engine_result":er})
            print(json.dumps({"engine_result":er}, indent=2))
            spend, _, oc, base, inc = spendable_drops(TAKER)
            if er == "tesSUCCESS":
                remaining -= slice_qty
        except Exception as e:
            attempts.append({"owner":row["owner"], "qty": str(slice_qty), "cap":cap, "engine_result":str(e)})
            print(f"Slice error: {e}")

    print("\n=== SUMMARY ===")
    print(json.dumps({"target_qty": str(BUY_QTY),
                      "remaining_unfilled": str(remaining),
                      "attempts": attempts}, indent=2))

if __name__ == "__main__":
    main()
