import os, json, time, requests
from decimal import Decimal

from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import autofill, sign
from xrpl.core import binarycodec

from xrpl.models.transactions import TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import (
    Ledger,
    Tx,
    AccountInfo,
    AccountLines,
    RipplePathFind,
)

# -------------------- env & client --------------------
load_dotenv(".env.testnet")
RPC         = os.getenv("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
ISSUER      = os.getenv("XRPL_ISSUER_ADDRESS")
CODE        = os.getenv("COPX_CODE", "COPX")

BUY_QTY     = Decimal(os.getenv("TAKER_BUY_AMOUNT_COPX", "250"))
SLIPPAGE    = Decimal(os.getenv("TAKER_SLIPPAGE", "0.02"))
POLL_EVERY  = float(os.getenv("XRPL_POLL_EVERY_S", "1.2"))
TX_TIMEOUT  = float(os.getenv("XRPL_TX_TIMEOUT_S", "45"))

client = JsonRpcClient(RPC)

# -------------------- small utils --------------------
def to160(code: str) -> str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40, "0")

CUR_HEX = to160(CODE)

def latest_validated_index() -> int:
    res = client.request(Ledger(ledger_index="validated")).result
    return int(res["ledger_index"])

def rpc(method: str, params: dict) -> dict:
    r = requests.post(RPC, json={"method": method, "params": [params]}, timeout=20)
    r.raise_for_status()
    out = r.json()
    if "result" in out:
        return out["result"]
    return out

# ----- normalize submit to always send a hex blob -----
def _extract_blob_from_signed(stx_any) -> str:
    # 1) SignedTransaction object has .tx_blob
    blob = getattr(stx_any, "tx_blob", None)
    if isinstance(blob, str) and all(c in "0123456789abcdefABCDEF" for c in blob):
        return blob
    # 2) Already hex string
    if isinstance(stx_any, str) and all(c in "0123456789abcdefABCDEF" for c in stx_any):
        return stx_any
    # 3) Signed JSON dict → encode (must contain signature)
    if isinstance(stx_any, dict):
        if not (stx_any.get("TxnSignature") and stx_any.get("SigningPubKey")):
            raise RuntimeError("tx_json not signed; missing TxnSignature/SigningPubKey")
        return binarycodec.encode(stx_any)
    # 4) Try to_xrpl then recurse
    to_x = getattr(stx_any, "to_xrpl", None)
    if callable(to_x):
        return _extract_blob_from_signed(to_x())
    raise RuntimeError(f"Cannot extract tx blob from type: {type(stx_any)}")

def submit_blob(stx_any) -> dict:
    blob = _extract_blob_from_signed(stx_any)
    return rpc("submit", {"tx_blob": blob})

def poll_tx_until_validated(txid: str, last_ledger_seq: int) -> dict:
    t0 = time.time()
    while True:
        if time.time() - t0 > TX_TIMEOUT:
            raise TimeoutError(f"Tx {txid} not validated within {TX_TIMEOUT}s")
        try:
            txr = client.request(Tx(transaction=txid)).result
            if txr.get("validated"):
                return txr
            cur = latest_validated_index()
            if cur >= last_ledger_seq:
                # Ledger window passed; return best info we have
                return {"validated": False, "tx_lookup": txr, "passed_last_ledger": True, "last_validated": cur}
        except Exception:
            pass
        time.sleep(POLL_EVERY)

def sign_autofill_and_submit(tx, wallet: Wallet) -> dict:
    atx = autofill(tx, client)
    stx = sign(atx, wallet)
    sres = submit_blob(stx)
    # attempt to get txid
    txid = (sres.get("tx_json") or {}).get("hash") or sres.get("hash") or getattr(stx, "hash", None)
    if not txid:
        # one more try: derive from signed json if present
        try:
            signed_json = stx.to_xrpl() if hasattr(stx, "to_xrpl") else None
            if isinstance(signed_json, dict):
                txid = binarycodec.decode(binarycodec.encode(signed_json))["hash"]
        except Exception:
            pass
    if not txid:
        raise RuntimeError(f"Submit response missing txid/hash: {json.dumps(sres, indent=2)}")
    return poll_tx_until_validated(txid, atx.last_ledger_sequence)

# -------------------- business helpers --------------------
def read_transfer_rate(issuer: str) -> int:
    # 1e9 (1000000000) means no fee; otherwise fee = (TransferRate - 1e9)/1e9
    ai = client.request(AccountInfo(account=issuer, ledger_index="validated", strict=True)).result
    acct = ai["account_data"]
    tr = int(acct.get("TransferRate", 1000000000))
    flags = int(acct.get("Flags", 0))
    return tr, flags

def ensure_trustline(addr: str, seed: str) -> dict:
    wal = Wallet.from_seed(seed)
    # if it already exists, skip
    lines = client.request(AccountLines(account=addr, ledger_index="validated")).result.get("lines", [])
    for ln in lines:
        if ln.get("account") == ISSUER and ln.get("currency") == CUR_HEX:
            return {"skipped": True, "line": ln}
    ts = TrustSet(
        account=addr,
        limit_amount=IssuedCurrencyAmount(currency=CUR_HEX, issuer=ISSUER, value="20000"),
    )
    return sign_autofill_and_submit(ts, wal)

def pathfind_quote(src: str, dest: str, amount_copx: Decimal) -> dict:
    # Ask rippled for a path that delivers IOU(COPX) to dest, paid by XRP from src
    req = RipplePathFind(
        source_account=src,
        destination_account=dest,
        destination_amount={"currency": CUR_HEX, "issuer": ISSUER, "value": str(amount_copx)},
    )
    return client.request(req).result

def build_payment(src: str, seed: str, dest: str, amount_copx: Decimal, slippage: Decimal) -> Payment:
    """
    Build a Payment that DELIVERs COPX to dest with a SendMax in XRP determined
    from pathfind quote plus slippage. Uses tfPartialPayment|tfImmediateOrCancel.
    """
    quote = pathfind_quote(src, dest, amount_copx)
    alts = quote.get("alternatives", [])
    if not alts:
        raise RuntimeError("No path alternatives returned by pathfind")
    # Pick the cheapest (first)
    best = alts[0]
    # SendMax must be XRP drops if the computed amount is XRP, or IssuedCurrencyAmount if IOU.
    # rippled returns "source_amount" which can be string (drops) or dict (IOU).
    src_amt = best.get("source_amount")
    if isinstance(src_amt, str):
        # XRP in drops string
        base_drops = int(src_amt)
        # add slippage
        smx = int((Decimal(base_drops) * (Decimal(1) + slippage)).to_integral_value())
        sendmax = str(smx)
    elif isinstance(src_amt, dict):
        # IOU path (unlikely for our scenario), add slippage to value
        val = Decimal(str(src_amt["value"])) * (Decimal(1) + slippage)
        sendmax = {
            "currency": src_amt["currency"],
            "issuer": src_amt.get("issuer") or src,
            "value": str(val),
        }
    else:
        raise RuntimeError(f"Unexpected source_amount shape: {src_amt}")

    flags = 0x00020000 | 0x00020000  # keep IOC (0x00020000); PartialPayment also 0x00020000 in old docs, but payment flag is 0x00020000; here IOC is meaningful for OfferCreate. We keep only tfPartialPayment for payment:
    flags = 0x00020000  # tfPartialPayment

    pay = Payment(
        account=src,
        destination=dest,
        amount=IssuedCurrencyAmount(currency=CUR_HEX, issuer=ISSUER, value=str(amount_copx)),
        send_max=sendmax,
        flags=flags,
        paths=best.get("paths_computed"),
    )
    return pay

# -------------------- main flow --------------------
def main():
    # 1) faucet a taker
    fr = requests.post("https://faucet.altnet.rippletest.net/accounts", json={}, timeout=15).json()
    seed = fr.get("seed")
    addr = (fr.get("account") or {}).get("classicAddress") or (fr.get("account") or {}).get("address")
    print("Taker:", addr)
    taker = Wallet.from_seed(seed)

    # 2) inspect issuer TransferRate (for logging)
    tr, fl = read_transfer_rate(ISSUER)
    print(f"Issuer TransferRate={tr} (1e9=no fee), Flags={fl}")

    # 3) ensure trustline
    tsr = ensure_trustline(addr, seed)
    if tsr.get("skipped"):
        print("TrustLine already existed.")
    else:
        print("TrustSet result:", tsr.get("meta", {}).get("TransactionResult") or tsr.get("engine_result") or tsr.get("result"))

    # 4) build a path Payment and submit
    #    (self-pay to keep funds; destination = taker)
    pay = build_payment(addr, seed, addr, BUY_QTY, SLIPPAGE)

    # sign + submit (hex blob), then poll
    res = sign_autofill_and_submit(pay, taker)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
# --- BEGIN PATCH: taker_buy_via_payment.py adjustments ---
# When pathfind returns no alternatives, snapshot top ask and place an IOC OfferCreate
# at cap = ceil(qty * (best_px * (1+slip))) in drops.

