import os, json, time, requests, math
from decimal import Decimal, ROUND_UP
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers, ServerState

load_dotenv(".env.testnet")
RPC     = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
CODE    = os.getenv("COPX_CODE","COPX")

BUY_QTY = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))  # COPX to buy
SLIP    = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))         # 0.02 = 2%
CUSH_D  = int(os.getenv("CAP_CUSHION_DROPS","20"))            # extra drops for rounding dust
FEE_D   = 10                                                  # default fee estimate in drops (adjust if needed)

client = JsonRpcClient(RPC)

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")
CUR = to160(CODE)

def faucet_new():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={})
    r.raise_for_status()
    p = r.json()
    seed = p.get("seed")
    addr = (p.get("account") or {}).get("classicAddress") or (p.get("account") or {}).get("address")
    if not seed or not addr:
        raise RuntimeError(f"Faucet payload missing seed/address:\n{json.dumps(p,indent=2)}")
    time.sleep(1.2)
    return addr, seed

def wait_seq(addr, timeout=10):
    t0=time.time()
    while time.time()-t0<timeout:
        ai = client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result
        if ai and "account_data" in ai:
            return ai["account_data"]
        time.sleep(0.8)
    raise TimeoutError("AccountInfo not ready")

def wait_trustline(addr, timeout=20):
    t0=time.time()
    while time.time()-t0<timeout:
        res = client.request(AccountLines(account=addr, ledger_index="validated")).result
        for ln in res.get("lines", []):
            if ln.get("currency")==CUR and ln.get("account")==ISSUER:
                return ln
        time.sleep(0.8)
    return None

def get_reserves():
    ss = client.request(ServerState()).result
    st = ((ss or {}).get("state") or {})
    vl = st.get("validated_ledger") or {}
    base = int(vl.get("reserve_base", 10000000))   # fallback 10 XRP in drops
    inc  = int(vl.get("reserve_inc", 2000000))     # fallback 2 XRP in drops
    return base, inc

def spendable_drops(addr):
    ad = client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result["account_data"]
    bal = int(ad["Balance"])
    owner_count = int(ad.get("OwnerCount", 0))
    base, inc = get_reserves()
    needed = base + owner_count * inc
    spend = bal - needed
    return max(spend, 0), {"balance":bal, "owner_count":owner_count, "reserve_base":base, "reserve_inc":inc, "needed":needed}

def _get(obj, *names):
    for n in names:
        if n in obj: return obj[n]
    return None

def _drops_from_amount(x):
    if isinstance(x, str):  # already drops
        return int(x)
    if isinstance(x, dict) and x.get("currency")=="XRP" and "value" in x:
        return int(Decimal(str(x["value"])) * Decimal(1_000_000))
    return None

def _iou_value(x):
    if isinstance(x, dict) and "value" in x:
        return Decimal(str(x["value"]))
    return None

def top_ask():
    # maker pays IOU (COPX), maker gets XRP => ASK book
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
        px = (Decimal(drops)/Decimal(1_000_000)) / copx  # XRP/COPX
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

    # 1) Trustline (so we can receive COPX)
    ts = TrustSet(
        account=addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
    )
    tsr = submit_tx(ts, taker)
    print("TrustSet result:", tsr.get("engine_result"))
    ln = wait_trustline(addr, timeout=20)
    if not ln:
        raise SystemExit("Trustline not established yet; stopping to avoid failed fill.")

    # 2) Top ask + compute target cap
    best = top_ask()
    if not best:
        print("No well-formed asks in the book; aborting.")
        return
    px, size = best
    eff_px   = px * (Decimal(1)+SLIP)  # worst price we accept
    target_cap_xrp  = BUY_QTY * eff_px
    target_cap_drops= round_drops(target_cap_xrp)

    # 3) Reserves-aware spendable guard
    spend, info = spendable_drops(addr)
    print(f"Spendable drops: {spend} (balance={info['balance']}, owner_count={info['owner_count']}, "
          f"reserve_base={info['reserve_base']}, reserve_inc={info['reserve_inc']})")

    max_drops_for_tx = max(spend - FEE_D, 0)  # leave room for fee
    if target_cap_drops > max_drops_for_tx:
        # clip BUY_QTY down to what fits the spendable cap
        # max_qty ≈ (max_drops_for_tx - cushion) / 1e6 / eff_px
        usable_drops = max(max_drops_for_tx - CUSH_D, 0)
        max_qty = (Decimal(usable_drops) / Decimal(1_000_000)) / eff_px
        if max_qty <= 0:
            print(f"Insufficient spendable XRP for any fill (need >{FEE_D+CUSH_D} drops). Aborting.")
            return
        # round down to, say, 6 decimals to avoid value-too-precise issues
        new_qty = max_qty.quantize(Decimal("0.000001"), rounding=ROUND_UP)  # small bias up, cap will still enforce limit
        print(f"Clipping buy size: requested {BUY_QTY} → {new_qty} COPX to respect spendable cap.")
        qty = new_qty
        cap_drops = min(usable_drops, round_drops(new_qty * eff_px))
    else:
        qty = BUY_QTY
        cap_drops = target_cap_drops

    print(f"Top ask ~ {px:.6f} XRP/COPX; paying up to {eff_px:.6f} for {qty} -> cap {(Decimal(cap_drops)/Decimal(1_000_000)):.6f} XRP ({cap_drops} drops)")

    # 4) BUY: pay XRP (taker_pays), get COPX (taker_gets), IOC
    tx = OfferCreate(
        account    = addr,
        taker_pays = str(cap_drops),  # XRP drops we are willing to pay (max)
        taker_gets = IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(qty)),
        flags      = 0x00020000  # tfImmediateOrCancel
    )
    res = submit_tx(tx, taker)
    print("IOC result:", json.dumps(res, indent=2))

    er = res.get("engine_result")
    if er in ("tecUNFUNDED_OFFER","tecKILLED"):
        print("Hint: If still unfunded or killed, increase spendable (fund more XRP), or increase slippage/cap slightly, or reduce qty.")

if __name__ == "__main__":
    main()
