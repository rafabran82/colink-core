import os, json, time, requests
from decimal import Decimal, ROUND_UP
from math import ceil
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, BookOffers
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC       = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
client    = JsonRpcClient(RPC)
ISSUER    = os.getenv("XRPL_ISSUER_ADDRESS")
CODE      = os.getenv("COPX_CODE", "COPX")
TARGET_Q  = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "1000"))   # desired COPX, we may downsize if not fillable
SLIPPAGE  = Decimal(os.getenv("TAKER_SLIPPAGE", "0.001"))         # 0.1%
LEDGER_PAUSE = float(os.getenv("LEDGER_SLEEP", "3.0"))
MAX_RETRIES  = int(os.getenv("SUBMIT_RETRIES", "2"))

def to160(code:str)->str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40, "0")

CUR = to160(CODE)

def faucet_new_account():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={})
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
            if line["currency"] == currency_hex and line["account"] == issuer:
                return True
        time.sleep(1.0)
    return False

def fetch_asks():
    # Maker GETS XRP, PAYS COPX  -> these are asks we can hit when we BUY COPX with XRP
    res = client.request(BookOffers(
        taker_gets={"currency": "XRP"},
        taker_pays={"currency": CUR, "issuer": ISSUER}
    )).result
    return res.get("offers", [])

def depth_fill_for_budget(target_qty_copx: Decimal, q_best: Decimal, slippage: Decimal):
    """
    Compute the executable COPX amount and the XRP budget (in drops) needed,
    walking the book until we either reach target_qty_copx or run out of depth,
    but never paying above q_best*(1+slippage).
    """
    cap_px = (q_best * (Decimal(1) + slippage)).quantize(Decimal("0.0000001"), rounding=ROUND_UP)

    offers = fetch_asks()
    if not offers:
        return Decimal(0), "0", cap_px

    total_copx = Decimal(0)
    total_xrp  = Decimal(0)

    for o in offers:
        # quality is quoted in XRP/COPX
        px = Decimal(str(o["quality"]))
        if px > cap_px:
            break  # beyond allowed price

        # Offer fields from book (maker side):
        # maker TakerPays = COPX available (value)
        # maker TakerGets = XRP (drops)
        maker_copx = Decimal(str(o["taker_pays"]["value"]))
        maker_xrp_drops = Decimal(str(o["taker_gets"]))  # already in drops
        # Derive amount-per-unit in drops per 1 COPX from this level:
        # price_px (XRP per COPX) => drops per COPX = px * 1_000_000
        drops_per_copx = (px * Decimal(1_000_000)).quantize(Decimal("1."), rounding=ROUND_UP)

        # How much can we take from this level?
        remaining = target_qty_copx - total_copx
        if remaining <= 0:
            break

        take_copx = maker_copx if maker_copx <= remaining else remaining

        # XRP drops needed for this slice
        need_drops = (take_copx * drops_per_copx)

        # Sanity: maker has at least that many drops available on their offer
        # (it should align, but be defensive)
        if need_drops > maker_xrp_drops:
            # clamp to maker's remaining drops
            take_copx = (maker_xrp_drops / drops_per_copx).quantize(Decimal("0.0000001"), rounding=ROUND_UP)
            if take_copx <= 0:
                continue
            need_drops = (take_copx * drops_per_copx)

        total_copx += take_copx
        total_xrp  += need_drops

        if total_copx >= target_qty_copx:
            break

    # Round XRP drops up to integer string
    cap_drops = str(int(ceil(total_xrp)))
    return total_copx, cap_drops, cap_px

def submit(tx, w, retries=MAX_RETRIES):
    last_err = None
    for _ in range(retries + 1):
        try:
            stx = sign(autofill(tx, client), w)
            res = submit_and_wait(stx, client).result
            return res
        except Exception as e:
            last_err = e
            time.sleep(LEDGER_PAUSE)
    raise last_err

def main():
    addr, seed = faucet_new_account()
    print("Taker:", addr)
    taker = Wallet.from_seed(seed)

    # 1) Trustline
    ts = TrustSet(
        account=addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
    )
    tsr = submit(ts, taker)
    print("TrustSet:", tsr.get("engine_result"))
    if not wait_trustline(addr, CUR, ISSUER, 25):
        raise SystemExit("Trustline not found yet; stopping to avoid PATH/UNFUNDED issues.")

    # 2) Read best ask and compute executable size under cap
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

    # 3) IOC BUY only the executable amount
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
