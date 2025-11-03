import os, json, time, requests
from decimal import Decimal, ROUND_UP
from math import ceil
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait, submit as submit_only
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, BookOffers
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")

RPC        = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
client     = JsonRpcClient(RPC)
ISSUER     = os.getenv("XRPL_ISSUER_ADDRESS")
CODE       = os.getenv("COPX_CODE", "COPX")
TARGET_Q   = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "1000"))
SLIPPAGE   = Decimal(os.getenv("TAKER_SLIPPAGE", "0.001"))
LEDGER_PAUSE = float(os.getenv("LEDGER_SLEEP", "3.0"))
MAX_RETRIES  = int(os.getenv("SUBMIT_RETRIES", "1"))

def to160(code:str)->str:
    if len(code) <= 3: return code
    b = code.encode("ascii")
    if len(b) > 20: raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40, "0")

CUR = to160(CODE)

def faucet_new_account():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={}, timeout=20)
    r.raise_for_status()
    p = r.json()
    seed = p.get("seed")
    classic = (p.get("account") or {}).get("classicAddress") or (p.get("account") or {}).get("address")
    if not seed or not classic:
        raise RuntimeError(f"Faucet payload missing seed/address:\n{json.dumps(p, indent=2)}")
    time.sleep(1.25)
    return classic, seed

def wait_trustline(addr, currency_hex, issuer, timeout_s=25):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        res = client.request(AccountLines(account=addr, ledger_index="validated")).result
        for line in res.get("lines", []):
            if line.get("currency") == currency_hex and line.get("account") == issuer:
                return True
        time.sleep(1.0)
    return False

def fetch_asks():
    res = client.request(BookOffers(
        taker_gets={"currency": "XRP"},
        taker_pays={"currency": CUR, "issuer": ISSUER}
    )).result
    return res.get("offers", [])

def _get_amount_value(amt):
    """
    Normalize rippled Amount shapes:
    - IOU dict => Decimal(value)
    - XRP string (drops) => Decimal(drops)
    """
    if isinstance(amt, dict):
        # IOU
        return Decimal(str(amt.get("value", "0")))
    # XRP in drops as string
    return Decimal(str(amt))

def _get_key(o, lower_key, upper_key):
    return o.get(lower_key) if lower_key in o else o.get(upper_key)

def depth_fill_for_budget(target_qty_copx: Decimal, q_best: Decimal, slippage: Decimal):
    cap_px = (q_best * (Decimal(1) + slippage)).quantize(Decimal("0.0000001"), rounding=ROUND_UP)
    offers = fetch_asks()
    if not offers:
        return Decimal(0), "0", cap_px

    total_copx = Decimal(0)
    total_xrp_drops  = Decimal(0)

    for idx, o in enumerate(offers):
        # tolerate key casing
        pays = _get_key(o, "taker_pays", "TakerPays")   # COPX (IOU)
        gets = _get_key(o, "taker_gets", "TakerGets")   # XRP (drops)
        if pays is None or gets is None or "quality" not in o:
            # malformed row; skip
            continue

        px = Decimal(str(o["quality"]))  # XRP/COPX
        if px > cap_px:
            break

        # maker PAYS = COPX quantity (IOU)
        try:
            maker_copx = _get_amount_value(pays)  # IOU .value
            maker_xrp_drops = _get_amount_value(gets)  # XRP drops
        except Exception:
            # unexpected shape; skip this row
            continue

        # sanity: IOU should be >= 0; XRP drops >= 0
        if maker_copx <= 0 or maker_xrp_drops <= 0:
            continue

        drops_per_copx = (px * Decimal(1_000_000)).quantize(Decimal("1."), rounding=ROUND_UP)

        remaining = target_qty_copx - total_copx
        if remaining <= 0:
            break

        take_copx = maker_copx if maker_copx <= remaining else remaining
        need_drops = (take_copx * drops_per_copx)

        # Guard against rounding beyond maker's available XRP drops on this level
        if need_drops > maker_xrp_drops:
            take_copx = (maker_xrp_drops / drops_per_copx).quantize(Decimal("0.0000001"), rounding=ROUND_UP)
            if take_copx <= 0:
                continue
            need_drops = (take_copx * drops_per_copx)

        total_copx += take_copx
        total_xrp_drops  += need_drops

        if total_copx >= target_qty_copx:
            break

    cap_drops = str(int(ceil(total_xrp_drops)))
    return total_copx, cap_drops, cap_px

def submit(tx, w, retries=MAX_RETRIES):
    last_err = None
    stx = sign(autofill(tx, client), w)
    for _ in range(retries + 1):
        try:
            return submit_and_wait(stx, client).result
        except Exception as e:
            last_err = e
            time.sleep(LEDGER_PAUSE)
    try:
        res = submit_only(stx, client)
        return getattr(res, "result", res)
    except Exception as e2:
        raise last_err or e2

def main():
    addr, seed = faucet_new_account()
    print("Taker:", addr)
    taker = Wallet.from_seed(seed)

    ts = TrustSet(
        account=addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
    )
    tsr = submit(ts, taker)
    print("TrustSet submit:", tsr.get("engine_result"))
    if not wait_trustline(addr, CUR, ISSUER, 25):
        raise SystemExit("Trustline not found yet; stopping to avoid PATH/UNFUNDED issues.")

    asks = fetch_asks()
    if not asks:
        print("No asks on book; nothing to take.")
        return
    q_best = Decimal(str(asks[0]["quality"]))

    exec_qty, cap_drops, cap_px = depth_fill_for_budget(TARGET_Q, q_best, SLIPPAGE)
    print(f"Best ask ~ {q_best} XRP/COPX; cap px {cap_px} XRP/COPX; "
          f"executable ≈ {exec_qty} COPX for {cap_drops} drops")

    if exec_qty <= 0:
        print("No executable quantity under cap; skipping IOC BUY.")
        return

    bid = OfferCreate(
        account=addr,
        taker_gets=cap_drops,  # XRP in drops (rounded up)
        taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(exec_qty)),
        flags=0x00020000  # tfImmediateOrCancel
    )
    br = submit(bid, taker)
    print("IOC BUY result:", json.dumps(br, indent=2))

if __name__ == "__main__":
    main()
