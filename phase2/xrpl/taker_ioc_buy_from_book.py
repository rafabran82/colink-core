import os, json, math
from decimal import Decimal, ROUND_UP
from dotenv import load_dotenv

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.account import get_balance
from xrpl.models.requests import AccountInfo, BookOffers, Ledger
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
HOT      = os.getenv("XRPL_HOT_ADDRESS")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
TSEED    = os.getenv("XRPL_TAKER_SEED")

CODE     = os.getenv("COPX_CODE","COPX")
BUY_QTY  = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX","250"))
SLIP     = Decimal(os.getenv("TAKER_SLIPPAGE","0.02"))       # 2%
CUSHION  = int(os.getenv("CAP_CUSHION_DROPS","20"))          # extra drops

TF_IOC   = 0x00020000  # tfImmediateOrCancel

def to160(code:str)->str:
    if len(code)<=3: return code
    b = code.encode("ascii")
    if len(b)>20: raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40,"0")

CUR = to160(CODE)

client = JsonRpcClient(RPC)
tw = Wallet.from_seed(TSEED)

def acct_root(addr:str):
    return client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result

def spendable_drops(addr:str):
    info = acct_root(addr)["account_data"]
    bal   = int(info["Balance"])
    oc    = int(info.get("OwnerCount", 0))
    # Testnet faucet reserves (base/inc) are high; read from validated ledger
    led = client.request(Ledger(ledger_index="validated", full=False, accounts=False, transactions=False, expand=False)).result
    base = int(led["ledger"]["reserve_base_xrp"]) * 1_000_000
    inc  = int(led["ledger"]["reserve_inc_xrp"])  * 1_000_000
    need = base + oc * inc
    return max(0, bal - need), bal, oc, base, inc

def ensure_trustline(addr:str, seed:str):
    # Create/ensure trustline to ISSUER/COPX (limit large enough)
    ts = TrustSet(
        account=addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
    )
    try:
        txr = submit_and_wait(sign(autofill(ts, client), Wallet.from_seed(seed)), client).result
        print("TrustSet result:", txr.get("engine_result"))
    except Exception as e:
        # Often returns temDST_IS_SRC if issuer==addr, or tec* if already present; treat as idempotent
        print("TrustSet result: already")

def first_executable_ask(taker:str):
    # Maker sells COPX (taker_pays=IC), receives XRP (taker_gets=XRP).
    book = client.request(BookOffers(
        taker=taker,
        taker_gets={"currency":"XRP"},
        taker_pays={"currency":CUR, "issuer":ISSUER},
        ledger_index="validated",
        limit=20
    )).result
    offers = book.get("offers", [])
    if not offers:
        return None, None

    # Pick first non-self owner; compute px and size
    for o in offers:
        owner = o.get("Account")
        if owner == taker or owner == HOT:
            continue
        tg = o.get("TakerGets")  # XRP (drops) as str or dict (should be str)
        tp = o.get("TakerPays")  # issued currency dict
        try:
            drops = int(tg) if isinstance(tg, str) else int(tg.get("value","0"))
        except Exception:
            # some servers return object for XRP; normalize
            if isinstance(tg, dict) and tg.get("currency") == "XRP":
                drops = int(tg.get("value","0"))
            else:
                continue
        if not isinstance(tp, dict): 
            continue
        val = Decimal(str(tp.get("value","0")))
        if val <= 0:
            continue
        px = Decimal(drops) / Decimal(1_000_000) / val   # XRP/COPX
        size = val
        return {"owner": owner, "px": px, "size": size}, o
    return None, None

def main():
    if not TAKER or not TSEED:
        print("Set XRPL_TAKER_ADDRESS and XRPL_TAKER_SEED.")
        return
    if HOT and TAKER == HOT:
        print("Refusing self-cross: TAKER equals HOT.")
        return
    print("Taker:", TAKER)

    # Ensure trustline (idempotent)
    ensure_trustline(TAKER, TSEED)

    # Spendable XRP
    spendable, bal, oc, base, inc = spendable_drops(TAKER)
    print(f"Spendable drops: {spendable} (balance={bal}, owner_count={oc}, reserve_base={base}, reserve_inc={inc})")

    # Find a non-self ask
    best, raw = first_executable_ask(TAKER)
    if not best:
        print("No executable asks from your perspective (either empty book or only self/HOT-owned).")
        return

    print(f"Chosen ask owner={best['owner']} px≈{best['px']:.6f} XRP/COPX size={best['size']} COPX")

    # Desired buy quantity (cannot exceed ask size)
    qty = min(BUY_QTY, best["size"])
    # Price cap with slippage
    cap_xrp = (best["px"] * qty * (Decimal(1) + SLIP)).quantize(Decimal("0.000001"), rounding=ROUND_UP)
    cap_drops = int((cap_xrp * Decimal(1_000_000)).to_integral_value(rounding=ROUND_UP)) + CUSHION
    cap_drops = min(cap_drops, spendable)  # cannot spend beyond spendable
    if cap_drops <= 0:
        print("Insufficient spendable XRP after reserves to place IOC.")
        return

    # Build IOC OfferCreate: taker (buyer) pays XRP (cap), gets COPX (qty)
    tx = OfferCreate(
        account=TAKER,
        taker_gets=str(cap_drops),  # we pay up to cap in XRP drops
        taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(qty)),  # we receive qty COPX
        flags=TF_IOC
    )

    # Use validated ledger + small cushion
    ai = acct_root(TAKER)
    vli = ai.get("ledger_index", None)
    # If account_info didn’t include it, fetch ledger explicitly
    if vli is None:
        vli = client.request(Ledger(ledger_index="validated")).result["ledger_index"]
    # autofill will set LastLedgerSequence; but we’ll let autofill do it based on validated+X.
    stx = sign(autofill(tx, client), tw)

    print(f"Submitting IOC (cap={cap_xrp} XRP ≈ {cap_drops} drops) for qty={qty} COPX …")
    res = submit_and_wait(stx, client).result
    print(json.dumps(res, indent=2))

    eng = res.get("engine_result","")
    if eng != "tesSUCCESS":
        print(f"Result: {eng} -> {res.get('engine_result_message','')}")
    else:
        txj = res.get("tx_json",{})
        print("✅ Filled or killed. Hash:", txj.get("hash"))
        # Optional: you could fetch account_lines to see updated COPX balance.

if __name__ == "__main__":
    main()
