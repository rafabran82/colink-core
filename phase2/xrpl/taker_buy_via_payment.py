import os, time, json, requests
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign
from xrpl.models.transactions import TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines, BookOffers, AccountInfo, Ledger, Tx
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")
RPC      = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
ISSUER   = os.getenv("XRPL_ISSUER_ADDRESS")
CODE     = os.getenv("COPX_CODE", "COPX")
AMOUNT   = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "250"))
SLIP     = Decimal(os.getenv("TAKER_SLIPPAGE", "0.02"))
CUSHION  = int(os.getenv("CAP_CUSHION_DROPS", "20"))
TX_TIMEOUT_S = int(os.getenv("XRPL_TX_TIMEOUT_S", "45"))
POLL_EVERY_S = float(os.getenv("XRPL_POLL_EVERY_S", "1.2"))

client = JsonRpcClient(RPC)

def to160(code:str)->str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40, "0")

CUR = to160(CODE)

def faucet_new():
    r = requests.post("https://faucet.altnet.rippletest.net/accounts", json={})
    r.raise_for_status()
    p = r.json()
    seed = p.get("seed")
    classic = (p.get("account") or {}).get("classicAddress") or (p.get("account") or {}).get("address")
    if not seed or not classic:
        raise RuntimeError(f"Faucet payload missing seed/address:\n{json.dumps(p,indent=2)}")
    time.sleep(1.2)
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

def issuer_transfer_rate(issuer):
    ai = client.request(AccountInfo(account=issuer, ledger_index="validated", strict=True)).result
    acct = ai.get("account_data", {})
    tr = int(acct.get("TransferRate", 1000000000))  # 1e9 == no fee
    flags = int(acct.get("Flags", 0))
    return tr, flags

def book_top_ask(taker_addr):
    res = client.request(BookOffers(
        taker_pays={"currency":"XRP"},
        taker_gets={"currency": CUR, "issuer": ISSUER},
        taker=taker_addr,
        ledger_index="current",
        limit=5
    )).result
    offers = res.get("offers", [])
    if not offers:
        return None

    def to_dec_xrp(a):
        if isinstance(a, str):
            return Decimal(a) / Decimal(1_000_000)
        if isinstance(a, dict) and a.get("currency") == "XRP":
            return Decimal(a["value"])
        raise ValueError("Unexpected XRP amount shape")

    def to_dec_iou(a):
        if isinstance(a, dict):
            return Decimal(str(a["value"]))
        raise ValueError("Unexpected IOU amount shape")

    top = offers[0]
    maker_pays_iou  = to_dec_iou(top["taker_pays"])
    maker_gets_xrp  = to_dec_xrp(top["taker_gets"])
    q = Decimal(str(top.get("quality"))) if "quality" in top else (maker_gets_xrp / maker_pays_iou)
    return {"q": q, "maker_iou": maker_pays_iou, "maker_xrp": maker_gets_xrp}

def latest_validated_index():
    led = client.request(Ledger(ledger_index="validated")).result
    return int(led["ledger_index"])

def rpc_submit_blob(stx_blob:str) -> dict:
    # Version-agnostic raw JSON-RPC submit
    r = requests.post(RPC, json={"method": "submit", "params": [{"tx_blob": stx_blob}]}, timeout=20)
    r.raise_for_status()
    out = r.json()
    # Some gateways wrap result under "result" or "result"/"engine_result"
    result = out.get("result") or out
    return result

def robust_submit(stx_blob:str, last_ledger_seq:int) -> dict:
    sres = rpc_submit_blob(stx_blob)
    txid = None
    tx_json = sres.get("tx_json") or {}
    txid = tx_json.get("hash") or sres.get("hash")
    if not txid:
        # Try to decode from blob failure response — still proceed to poll if unknown
        raise RuntimeError(f"Submit response missing txid/hash: {json.dumps(sres, indent=2)}")

    t0 = time.time()
    while True:
        if time.time() - t0 > TX_TIMEOUT_S:
            raise TimeoutError(f"Transaction {txid} not validated within {TX_TIMEOUT_S}s")

        try:
            txr = client.request(Tx(transaction=txid)).result
        except Exception:
            time.sleep(POLL_EVERY_S)
            continue

        if txr.get("validated"):
            return txr

        cur_val = latest_validated_index()
        if cur_val >= last_ledger_seq:
            return {
                "validated": False,
                "last_validated": cur_val,
                "last_ledger_sequence": last_ledger_seq,
                "note": "LastLedgerSequence passed without validation",
                "submit_response": sres,
                "tx_lookup": txr,
            }

        time.sleep(POLL_EVERY_S)

def sign_autofill_and_submit(tx, wallet: Wallet) -> dict:
    atx = autofill(tx, client)
    stx = sign(atx, wallet)
    return robust_submit(stx.to_xrpl(), atx.last_ledger_sequence)

def main():
    taker_addr, taker_seed = faucet_new()
    taker = Wallet.from_seed(taker_seed)
    print("Taker:", taker_addr)

    tr, flags = issuer_transfer_rate(ISSUER)
    print(f"Issuer TransferRate={tr} (1e9=no fee), Flags={flags}")

    # 1) Trust line
    ts = TrustSet(
        account=taker_addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value="20000")
    )
    ts_txr = sign_autofill_and_submit(ts, taker)
    print("TrustSet result:", json.dumps(ts_txr, indent=2))
    if not wait_trustline(taker_addr, CUR, ISSUER, 25):
        raise SystemExit("Trustline not visible yet; aborting to avoid path issues.")

    # 2) Read top ask
    top = book_top_ask(taker_addr)
    if not top:
        print("No asks on the book; nothing to take right now.")
        return
    q = top["q"]  # XRP/COPX

    # Include TransferRate defensively
    eff_q = (q * Decimal(tr) / Decimal(1_000_000_000)).quantize(Decimal("0.0000001"), rounding=ROUND_UP)
    cap_px = (eff_q * (Decimal(1) + SLIP)).quantize(Decimal("0.0000001"), rounding=ROUND_UP)

    # Budget
    xrp_cap  = (AMOUNT * cap_px).quantize(Decimal("0.000001"), rounding=ROUND_UP)
    drops_cap = int((xrp_cap * Decimal(1_000_000)).to_integral_value(rounding=ROUND_UP)) + CUSHION
    deliver_min = (AMOUNT * (Decimal(1) - SLIP)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

    print(f"Top ask ~ {q} XRP/COPX; eff cap px {cap_px} XRP/COPX; SendMax {drops_cap} drops; DeliverMin {deliver_min} {CODE}")

    pay = Payment(
        account=taker_addr,
        destination=taker_addr,
        amount=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(AMOUNT)),
        send_max=str(drops_cap),  # drops as string
        deliver_min=IssuedCurrencyAmount(currency=CUR, issuer=ISSUER, value=str(deliver_min)),
        flags=0x00020000          # tfPartialPayment
    )

    pay_txr = sign_autofill_and_submit(pay, taker)
    print("PAYMENT result:", json.dumps(pay_txr, indent=2))

if __name__ == "__main__":
    main()
# --- PATCH: robust submit accepts tx blob or signed JSON and encodes if needed ---
from xrpl.core import binarycodec  # add near imports at top if not present

def _extract_blob_from_signed(stx_any) -> str:
    """
    Accepts: SignedTransaction object, hex string, or signed tx JSON (dict).
    Returns: hex blob suitable for rippled `submit` tx_blob.
    """
    # 1) SignedTransaction object with tx_blob
    try:
        blob = getattr(stx_any, "tx_blob", None)
        if isinstance(blob, str) and all(c in "0123456789ABCDEFabcdef" for c in blob):
            return blob
    except Exception:
        pass

    # 2) Already a hex string
    if isinstance(stx_any, str) and all(c in "0123456789ABCDEFabcdef" for c in stx_any):
        return stx_any

    # 3) Signed JSON dict → encode to blob
    if isinstance(stx_any, dict):
        # Must already contain a signature
        if not (stx_any.get("TxnSignature") and stx_any.get("SigningPubKey")):
            raise RuntimeError("Provided tx_json is not signed; missing TxnSignature/SigningPubKey.")
        # Encode to binary hex using binarycodec
        return binarycodec.encode(stx_any)

    # 4) Fallback: try to_xrpl() then recurse
    to_x = getattr(stx_any, "to_xrpl", None)
    if callable(to_x):
        return _extract_blob_from_signed(to_x())

    raise RuntimeError(f"Cannot extract tx blob from type: {type(stx_any)}")

def rpc_submit_blob(stx_any) -> dict:
    """
    Accepts mixed signed tx representations, normalizes to hex blob, then POSTs JSON-RPC submit.
    """
    blob = _extract_blob_from_signed(stx_any)
    r = requests.post(RPC, json={"method": "submit", "params": [{"tx_blob": blob}]}, timeout=20)
    r.raise_for_status()
    out = r.json()
    return out.get("result") or out

def sign_autofill_and_submit(tx, wallet: Wallet) -> dict:
    atx = autofill(tx, client)
    stx = sign(atx, wallet)
    # Hand the SignedTransaction object directly; rpc_submit_blob will normalize it
    sres = rpc_submit_blob(stx)
    # Try to get the txid for polling
    txid = (sres.get("tx_json") or {}).get("hash") or sres.get("hash")
    if not txid:
        # If hash missing, try to pull it from the signed tx object
        txid = getattr(stx, "hash", None)

    if not txid:
        # As a last resort, poll encode(atx) hash-less, but we still can continue with LastLedgerSequence
        raise RuntimeError(f"Submit response missing txid/hash: {json.dumps(sres, indent=2)}")

    last_ledger_seq = atx.last_ledger_sequence
    # Poll for validation
    t0 = time.time()
    while True:
        if time.time() - t0 > TX_TIMEOUT_S:
            raise TimeoutError(f"Transaction {txid} not validated within {TX_TIMEOUT_S}s")

        try:
            txr = client.request(Tx(transaction=txid)).result
        except Exception:
            time.sleep(POLL_EVERY_S)
            continue

        if txr.get("validated"):
            return txr

        cur_val = latest_validated_index()
        if cur_val >= last_ledger_seq:
            return {
                "validated": False,
                "last_validated": cur_val,
                "last_ledger_sequence": last_ledger_seq,
                "note": "LastLedgerSequence passed without validation",
                "submit_response": sres,
                "tx_lookup": txr,
            }

        time.sleep(POLL_EVERY_S)
