import os, json, math
from decimal import Decimal
from dotenv import load_dotenv

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import (
    AccountInfo,
    BookOffers,
    ServerState,
)

TF_IOC = 0x00020000  # tfImmediateOrCancel

def to160(code: str) -> str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("currency code > 20 bytes")
    return b.hex().upper().ljust(40, "0")

def server_reserves_xrp(client: JsonRpcClient):
    st = client.request(ServerState()).result
    # Prefer validated_ledger if present; fall back gracefully
    v = st.get("state", {}).get("validated_ledger", {})
    base = v.get("reserve_base_xrp")
    inc  = v.get("reserve_inc_xrp")
    if base is None or inc is None:
        # very old servers might differ; set sane testnet defaults
        base, inc = "10", "2"
    return Decimal(str(base)), Decimal(str(inc))

def spendable_drops(client: JsonRpcClient, account: str) -> tuple[int, int, int, int, int]:
    info = client.request(AccountInfo(account=account, ledger_index="validated")).result
    ad = info["account_data"]
    balance_drops = int(ad["Balance"])
    owner_count   = int(ad.get("OwnerCount", 0))

    base_xrp, inc_xrp = server_reserves_xrp(client)
    reserve_base_drops = int(base_xrp * Decimal(1_000_000))
    reserve_inc_drops  = int(inc_xrp  * Decimal(1_000_000))
    needed = reserve_base_drops + owner_count * reserve_inc_drops
    spendable = max(0, balance_drops - needed)
    return spendable, balance_drops, owner_count, reserve_base_drops, reserve_inc_drops

def ensure_trustline(client: JsonRpcClient, taker_addr: str, taker_seed: str, issuer: str, code160: str, limit: str = "20000"):
    # Lightweight: just send a TrustSet; if it already exists, XRPL returns "tecNO_LINE_REDUNDANT" or it may just be already present.
    w = Wallet.from_seed(taker_seed)
    ts = TrustSet(
        account=taker_addr,
        limit_amount=IssuedCurrencyAmount(currency=code160, issuer=issuer, value=limit),
        flags=0
    )
    stx = sign(autofill(ts, client), w)
    try:
        res = submit_and_wait(stx, client).result
        print(f"TrustSet result: {res.get('engine_result')}")
    except Exception as e:
        # Some nodes/versions return tem/tec for redundant lines; not fatal for our flow.
        print(f"TrustSet result: {e}")

def best_ask_for_taker(client: JsonRpcClient, taker: str, issuer: str, code160: str):
    # Maker sells COPX (IC), receives XRP. From taker perspective: taker_gets=XRP, taker_pays=IC
    # (This is the BookOffers direction for asks.)
    book = client.request(BookOffers(
        taker=taker,
        taker_gets={"currency": "XRP"},
        taker_pays={"currency": code160, "issuer": issuer},
        ledger_index="validated",
        limit=20
    )).result

    offers = book.get("offers", []) or []
    if not offers:
        return None

    # Filter anything owned by the taker, just in case.
    filtered = [o for o in offers if o.get("Account") != taker]
    if not filtered:
        return None

    # The "best" is the top entry as returned by XRPL for asks.
    return filtered[0]

def main():
    load_dotenv(".env.testnet")
    RPC     = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    ISSUER  = os.getenv("XRPL_ISSUER_ADDRESS")
    ISEED   = os.getenv("XRPL_ISSUER_SEED")
    HOT     = os.getenv("XRPL_HOT_ADDRESS")
    MAKER   = os.getenv("XRPL_MAKER_ADDRESS")
    MSEED   = os.getenv("XRPL_MAKER_SEED")
    TAKER   = os.getenv("XRPL_TAKER_ADDRESS")
    TSEED   = os.getenv("XRPL_TAKER_SEED")
    CODE    = os.getenv("COPX_CODE", "COPX")

    if not TAKER or not TSEED:
        print("Set XRPL_TAKER_ADDRESS and XRPL_TAKER_SEED.")
        return
    if HOT and TAKER == HOT:
        print("Taker must differ from HOT to avoid self-cross.")
        return

    CUR = to160(CODE)
    client = JsonRpcClient(RPC)

    print(f"Taker: {TAKER}")

    # 1) Ensure trustline
    ensure_trustline(client, TAKER, TSEED, ISSUER, CUR)

    # 2) Compute spendable drops (safety)
    spendable, bal, oc, base, inc = spendable_drops(client, TAKER)
    print(f"Spendable drops: {spendable} (balance={bal}, owner_count={oc}, reserve_base={base}, reserve_inc={inc})")

    # 3) Find best executable ask (non-self)
    ask = best_ask_for_taker(client, TAKER, ISSUER, CUR)
    if not ask:
        print("No executable asks from your perspective (likely none or only self-owned present).")
        return

    # Ask fields: maker wants to GET XRP (drops) and PAY COPX (IC).
    tg = ask.get("TakerGets")
    tp = ask.get("TakerPays")
    # According to BookOffers docs, for the direction we requested:
    # TakerGets => XRP (drops string), TakerPays => IC {value, issuer, currency}
    try:
        maker_drops = int(tg) if isinstance(tg, str) else int(tg.get("value", "0"))
    except Exception:
        # Some servers may return uppercase keys
        maker_drops = int(ask.get("taker_gets")) if isinstance(ask.get("taker_gets"), str) else int(ask.get("taker_gets", {}).get("value", "0"))

    ic = tp if isinstance(tp, dict) else ask.get("taker_pays", {})
    size_copx = Decimal(ic.get("value", "0"))
    maker = ask.get("Account", "")

    if size_copx <= 0 or maker_drops <= 0:
        print("Top ask had non-positive size/pricing; abort.")
        return

    best_px = Decimal(maker_drops) / (size_copx * Decimal(1_000_000))  # XRP/COPX
    print(f"Chosen ask owner={maker} px≈{best_px:.6f} XRP/COPX size={size_copx} COPX")

    # 4) Build IOC buy for the requested qty
    qty = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "250"))
    slip = Decimal(os.getenv("TAKER_SLIPPAGE", "0.02"))
    cushion = int(os.getenv("CAP_CUSHION_DROPS", "20"))

    pay_px = best_px * (Decimal(1) + slip)
    cap_xrp = (qty * pay_px)
    cap_drops = int((cap_xrp * Decimal(1_000_000)).to_integral_value(rounding="ROUND_UP")) + cushion

    print(f"Submitting IOC (cap={cap_xrp:.6f} XRP ≈ {cap_drops} drops) for qty={qty} COPX …")

    if cap_drops > spendable:
        print(f"Cap {cap_drops} drops exceeds spendable {spendable} drops; abort.")
        return

    w = Wallet.from_seed(TSEED)
    tx = OfferCreate(
        account=TAKER,
        # BUYING COPX: pay XRP (drops), get COPX (IC)
        taker_pays=str(cap_drops),
        taker_gets=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(qty)),
        flags=TF_IOC
    )
    stx = sign(autofill(tx, client), w)
    res = submit_and_wait(stx, client).result

    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "engine_message": res.get("engine_result_message"),
        "txid": res.get("tx_json", {}).get("hash"),
        "last_ledger": res.get("validated_ledger_index")
    }, indent=2))

if __name__ == "__main__":
    main()
