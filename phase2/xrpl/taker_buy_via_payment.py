import os, json, re
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import (
    AccountInfo, AccountLines, BookOffers, ServerState, RipplePathFind
)
from xrpl.models.transactions import Payment, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
CODE_ASC = os.getenv("COPX_CODE","COPX")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
TAKER_SD = os.getenv("XRPL_TAKER_SEED")

BUY_QTY  = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIP     = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))
CUSHION  = int(os.getenv("CAP_CUSHION_DROPS","20"))
USE_LIMIT_QUALITY = bool(int(os.getenv("USE_LIMIT_QUALITY","0")))

client = JsonRpcClient(RPC)

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CODE160 = to160(CODE_ASC)

def _drops_from_xrp(x):
    return int((Decimal(str(x))*Decimal(1_000_000)).to_integral_value())

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

def best_px():
    res = client.request(BookOffers(
        taker=TAKER,
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CODE160,"issuer":ISSUER},
        ledger_index="validated",
        limit=10
    )).result
    offers = res.get("offers",[]) or []
    best=None
    for o in offers:
        tp = o.get("taker_pays") or o.get("TakerPays")
        tg = o.get("taker_gets") or o.get("TakerGets")
        if not isinstance(tp, dict):
            continue
        size = Decimal(str(tp.get("value","0")))
        if size<=0:
            continue
        if isinstance(tg,str) and re.fullmatch(r"\d+",tg):
            drops=int(tg)
        elif isinstance(tg,dict) and (tg.get("currency","").upper()=="XRP"):
            drops=_drops_from_xrp(tg["value"])
        else:
            continue
        px = (Decimal(drops)/Decimal(1_000_000))/size
        if (best is None) or (px<best): best=px
    return best

TF_PARTIAL_PAYMENT = 0x00020000
TF_LIMIT_QUALITY  = 0x00040000

def ensure_trustline():
    try:
        ts = TrustSet(
            account=TAKER,
            limit_amount=IssuedCurrencyAmount(currency=CODE160, issuer=ISSUER, value=str(10_000_000))
        )
        r = submit_and_wait(sign(autofill(ts, client), Wallet.from_seed(TAKER_SD)), client).result
        print(f"TrustSet result: {r.get('engine_result') or 'already'}")
    except Exception:
        print("TrustSet result: already")

def compute_paths(amount_ic):
    # IMPORTANT: use source_currencies (XRP) instead of source_amount (not supported by your xrpl-py)
    req = RipplePathFind(
        source_account=TAKER,
        destination_account=TAKER,
        destination_amount=amount_ic,
        source_currencies=[{"currency":"XRP"}],
        ledger_index="validated"
    )
    res = client.request(req).result
    alts = res.get("alternatives",[]) or []
    print(f"[pathfind] alternatives returned: {len(alts)}")
    return alts

def main():
    if not TAKER or not TAKER_SD:
        print("Set XRPL_TAKER_ADDRESS and XRPL_TAKER_SEED.")
        return

    print(f"Taker: {TAKER}")
    ensure_trustline()

    spend, bal, oc, base, inc = spendable_drops(TAKER)
    print(f"Spendable drops: {spend} (balance={bal}, owner_count={oc}, reserve_base={base}, reserve_inc={inc})")

    px = best_px()
    if px is None:
        print("No asks available.")
        return

    # No issuer TransferRate on your dump; fee_mult = 1
    worst = px*(Decimal(1)+SLIP)
    cap_drops = _drops_from_xrp(BUY_QTY*worst) + CUSHION
    if cap_drops > spend:
        print(f"Cap {cap_drops} exceeds spendable {spend}. Reduce qty/slippage or add XRP.")
        return

    amount_ic = {
        "currency": CODE160,
        "issuer": ISSUER,
        "value": str(BUY_QTY)
    }

    alts = compute_paths(amount_ic)
    if not alts:
        print("No paths returned by server (PATH_DRY likely) — try again later or increase cap slightly.")
        return

    path = alts[0].get("paths_computed", [])
    flags = TF_PARTIAL_PAYMENT | (TF_LIMIT_QUALITY if USE_LIMIT_QUALITY else 0)

    pay = Payment(
        account=TAKER,
        destination=TAKER,
        amount=IssuedCurrencyAmount(**amount_ic),
        send_max=str(cap_drops),
        flags=flags,
        paths=path
    )
    stx = sign(autofill(pay, client), Wallet.from_seed(TAKER_SD))
    res = submit_and_wait(stx, client).result
    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "cap_drops": cap_drops,
        "px_best": f"{px:.6f}",
        "px_worst_effective": f"{worst:.6f}",
        "used_limit_quality": bool(flags & TF_LIMIT_QUALITY),
        "used_paths": bool(path)
    }, indent=2))

if __name__ == "__main__":
    main()
