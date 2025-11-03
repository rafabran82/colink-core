import os, json, time, requests
from decimal import Decimal, ROUND_UP
from math import ceil
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign, submit_and_wait, submit as submit_only
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, BookOffers, AccountInfo, Ledger
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")

RPC          = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
client       = JsonRpcClient(RPC)
ISSUER       = os.getenv("XRPL_ISSUER_ADDRESS")
CODE         = os.getenv("COPX_CODE", "COPX")
TARGET_Q     = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "250"))
SLIPPAGE     = Decimal(os.getenv("TAKER_SLIPPAGE", "0.02"))  # e.g., 2% during testing
LEDGER_PAUSE = float(os.getenv("LEDGER_SLEEP", "3.0"))
MAX_RETRIES  = int(os.getenv("SUBMIT_RETRIES", "1"))         # one retry after cap bump
CAP_CUSHION_DROPS = int(os.getenv("CAP_CUSHION_DROPS", "20"))# small dust cushion in drops
RETRY_CAP_BUMP_PCT = Decimal(os.getenv("RETRY_CAP_BUMP_PCT", "0.01"))  # +1% on retry

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
    time.sleep(1.5)
    return classic, seed

def wait_for_account(addr: str, timeout_s=30):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            ai = client.request(AccountInfo(account=addr, ledger_index="validated", strict=True)).result
            seq = int(ai["account_data"]["Sequence"])
            led = int(client.request(Ledger(ledger_index="validated")).result["ledger_index"])
            return seq, led
        except Exception:
            time.sleep(1.0)
    raise TimeoutError("AccountInfo not available yet; faucet funding not fully validated?")

def get_issuer_settings(issuer:str):
    ai = client.request(AccountInfo(account=issuer, ledger_index="validated", strict=True)).result
    ad = ai["account_data"]
    # TransferRate: 1_000_000_000 = no fee; > that means fee
    tr = int(ad.get("TransferRate", 1000000000))
    flags = int(ad.get("Flags", 0))
    return tr, flags

def get_trustline(addr:str, currency_hex:str, issuer:str):
    res = client.request(AccountLines(account=addr, ledger_index="validated")).result
    for line in res.get("lines", []):
        if line.get("currency") == currency_hex and line.get("account") == issuer:
            return line
    return None

def wait_trustline(addr, currency_hex, issuer, timeout_s=25):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if get_trustline(addr, currency_hex, issuer):
            return True
        time.sleep(1.0)
    return False

def fetch_asks():
    return client.request(BookOffers(
        taker_gets={"currency": "XRP"},
        taker_pays={"currency": CUR, "issuer": ISSUER}
    )).result.get("offers", [])

def _get_amount_value(amt):
    # IOU dict -> Decimal(value) ; XRP string (drops) -> Decimal(drops)
    if isinstance(amt, dict):
        return Decimal(str(amt.get("value", "0")))
    return Decimal(str(amt))

def _get_key(o, lower_key, upper_key):
    return o.get(lower_key) if lower_key in o else o.get(upper_key)

def effective_px_with_tr(quality_xrp_per_copx: Decimal, transfer_rate: int) -> Decimal:
    """Apply issuer TransferRate (billionths). 1_000_000_000 means no fee."""
    if transfer_rate <= 0:
        transfer_rate = 1000000000
    factor = Decimal(transfer_rate) / Decimal(1000000000)
    return (quality_xrp_per_copx * factor)

def depth_fill_for_budget(target_qty_copx: Decimal, q_best: Decimal, slippage: Decimal, transfer_rate:int):
    # cap price includes slippage and issuer TR
    cap_px = effective_px_with_tr(q_best, transfer_rate) * (Decimal(1) + slippage)
    cap_px = cap_px.quantize(Decimal("0.0000001"), rounding=ROUND_UP)

    offers = fetch_asks()
    if not offers:
        return Decimal(0), "0", cap_px

    total_copx = Decimal(0)
    total_xrp_drops  = Decimal(0)

    for o in offers:
        pays = _get_key(o, "taker_pays", "TakerPays")   # COPX (IOU)
        gets = _get_key(o, "taker_gets", "TakerGets")   # XRP (drops)
        if pays is None or gets is None or "quality" not in o:
            continue

        raw_px = Decimal(str(o["quality"]))          # XRP/COPX (book)
        px = effective_px_with_tr(raw_px, transfer_rate)

        if px > cap_px:
            break

        try:
            maker_copx = _get_amount_value(pays)
            maker_xrp_drops = _get_amount_value(gets)
        except Exception:
            continue

        if maker_copx <= 0 or maker_xrp_drops <= 0:
            continue

        drops_per_copx = (px * Decimal(1_000_000)).quantize(Decimal("1."), rounding=ROUND_UP)

        remaining = target_qty_copx - total_copx
        if remaining <= 0:
            break

        take_copx = maker_copx if maker_copx <= remaining else remaining
        need_drops = (take_copx * drops_per_copx)

        if need_drops > maker_xrp_drops:
            # trim to maker limit
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

def submit_fresh(tx_builder, wallet, addr):
    """
    Fresh autofill+sign each attempt, set LastLedgerSequence from current validated,
    and retry once on transient issues. On final failure, raw-submit the last build.
    """
    last_err = None
    for _ in range(MAX_RETRIES + 1):
        try:
            _, led = wait_for_account(addr, timeout_s=30)
            tx = tx_builder()
            tx.last_ledger_sequence = led + 20
            stx = sign(autofill(tx, client), wallet)
            res = submit_and_wait(stx, client).result
            er = str(res.get("engine_result", ""))
            # anything tes* is good; tecKILLED means IOC didn’t match — return for caller to decide
            if er.startswith("tes") or er == "tecKILLED":
                return res
            last_err = RuntimeError(f"engine_result: {er}")
        except Exception as e:
            last_err = e
        time.sleep(LEDGER_PAUSE)
    try:
        tx = tx_builder()
        stx = sign(autofill(tx, client), wallet)
        raw = submit_only(stx, client)
        return getattr(raw, "result", raw)
    except Exception as e2:
        raise last_err or e2

def main():
    addr, seed = faucet_new_account()
    print("Taker:", addr)
    taker = Wallet.from_seed(seed)

    # Issuer diagnostics
    tr, flags = get_issuer_settings(ISSUER)
    print(f"Issuer TransferRate={tr} (1e9=no fee), Flags={flags}")

    # 1) Trustline
    def _trust_tx():
        return TrustSet(
            account=addr,
            limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
        )
    tsr = submit_fresh(_trust_tx, taker, addr)
    print("TrustSet result:", tsr.get("engine_result"))
    if not wait_trustline(addr, CUR, ISSUER, 25):
        raise SystemExit("Trustline not found yet; stopping.")

    # show trustline
    tl = get_trustline(addr, CUR, ISSUER)
    print("TrustLine:", json.dumps(tl, indent=2))

    # 2) Discover best ask and compute executable slice/cap (refetch right before submit)
    asks = fetch_asks()
    if not asks:
        print("No asks on book; nothing to take.")
        return
    q_best = Decimal(str(asks[0]["quality"]))
    exec_qty, cap_drops, cap_px = depth_fill_for_budget(TARGET_Q, q_best, SLIPPAGE, tr)

    # add tiny dust cushion to cap in drops
    cap_drops_int = int(cap_drops) + CAP_CUSHION_DROPS
    cap_drops = str(cap_drops_int)

    print(f"Best ask ~ {q_best} XRP/COPX; eff cap px {cap_px} XRP/COPX;"
          f" executable ≈ {exec_qty} COPX for {cap_drops} drops (incl. cushion {CAP_CUSHION_DROPS})")

    if exec_qty <= 0:
        print("No executable quantity under cap; skipping IOC BUY.")
        return

    # 3) IOC BUY — build with a fresh snapshot again just before signing
    def _ioc_tx_builder(drops_str, qty_str):
        def _builder():
            return OfferCreate(
                account=addr,
                taker_gets=drops_str,  # XRP in drops
                taker_pays=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=qty_str),
                flags=0x00020000  # tfImmediateOrCancel
            )
        return _builder

    # first attempt
    br = submit_fresh(_ioc_tx_builder(cap_drops, str(exec_qty)), taker, addr)
    print("IOC BUY result:", json.dumps(br, indent=2))

    if str(br.get("engine_result")) == "tecKILLED":
        # retry once with a +1% cap bump in drops
        bumped = str(int(Decimal(cap_drops) * (Decimal(1) + RETRY_CAP_BUMP_PCT)))
        print(f"Retrying once with +{RETRY_CAP_BUMP_PCT*100}% cap -> {bumped} drops …")
        br2 = submit_fresh(_ioc_tx_builder(bumped, str(exec_qty)), taker, addr)
        print("IOC BUY retry result:", json.dumps(br2, indent=2))

if __name__ == "__main__":
    main()
