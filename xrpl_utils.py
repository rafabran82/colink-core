import json
from decimal import Decimal
from typing import Dict, Any, List

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models import requests as req
from xrpl.models.transactions import Payment, TrustSet, OfferCreate, OfferCancel
from xrpl.models.currencies import XRP as XRPModel
from xrpl.utils import xrp_to_drops
from xrpl.transaction import autofill, sign, submit_and_wait

# Try to import the reliable-submission exception; if not available in this xrpl-py version, define a stub
try:
    from xrpl.transaction.reliable_submission import XRPLReliableSubmissionException as _RSEx
except Exception:  # pragma: no cover
    class _RSEx(Exception):  # fallback
        pass

def sign_submit(tx, wallet: Wallet, client: JsonRpcClient):
    """
    Autofill + sign + reliable submit. Never throws; returns dict with either:
      { "ok": True,  "engine": <result dict> } on success
      { "ok": False, "error": "...", "type": "ExceptionClass", "engine": <partial or None> } on error
    """
    try:
        filled = autofill(tx, client)
        signed = sign(filled, wallet)
        res = submit_and_wait(signed, client).result
        return {"ok": True, "engine": res}
    except _RSEx as e:
        payload = getattr(e, "result", None) if hasattr(e, "result") else None
        return {"ok": False, "type": "_RSEx", "error": str(e), "engine": payload}
    except Exception as e:
        return {"ok": False, "type": e.__class__.__name__, "error": str(e), "engine": None}

def client_from(url: str) -> JsonRpcClient:
    return JsonRpcClient(url)

def wallet_from_seed(seed: str) -> Wallet:
    return Wallet.from_seed(seed)

def addr_from_seed(seed: str) -> str:
    return wallet_from_seed(seed).classic_address

def get_xrp_balance(client: JsonRpcClient, address: str) -> int:
    r = client.request(req.AccountInfo(account=address, ledger_index="validated", strict=True))
    return int(r.result["account_data"]["Balance"])

def get_account_lines(client: JsonRpcClient, address: str) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    marker = None
    while True:
        r = client.request(req.AccountLines(account=address, ledger_index="validated", limit=400, marker=marker))
        lines.extend(r.result.get("lines", []))
        marker = r.result.get("marker")
        if not marker:
            break
    return lines

def fetch_col_state(client: JsonRpcClient, trader_seed: str, issuer_addr: str, currency: str):
    trader_addr = addr_from_seed(trader_seed)
    ixrp = get_xrp_balance(client, issuer_addr)
    txrp = get_xrp_balance(client, trader_addr)
    lines = get_account_lines(client, trader_addr)
    ious = [l for l in lines if l.get("account") == issuer_addr and l.get("currency") == currency]
    return {
        "issuer": {"address": issuer_addr, "xrp_drops": ixrp},
        "trader": {"address": trader_addr, "xrp_drops": txrp, "ious": ious},
    }

def ensure_trustline(client: JsonRpcClient, trader_seed: str, issuer_addr: str, currency: str, limit: str):
    w = wallet_from_seed(trader_seed)
    tx = TrustSet(
        account=w.classic_address,
        limit_amount={"currency": currency, "issuer": issuer_addr, "value": str(limit)},
    )
    return sign_submit(tx, w, client)

def iou_payment(client: JsonRpcClient, issuer_seed: str, dest: str, currency: str, amount: str):
    w = wallet_from_seed(issuer_seed)
    tx = Payment(
        account=w.classic_address,
        destination=dest,
        amount={"currency": currency, "issuer": w.classic_address, "value": str(amount)},
    )
    return sign_submit(tx, w, client)

def create_offer(client: JsonRpcClient, side: str, trader_seed: str, issuer_addr: str, currency: str, iou_amt: str, xrp_amt: str):
    """
    SELL_COL (sell COL for XRP): Maker offers COL, wants XRP
        -> taker_pays = COL, taker_gets = XRP
    BUY_COL  (buy COL with XRP): Maker offers XRP, wants COL
        -> taker_pays = XRP, taker_gets = COL
    """
    w = wallet_from_seed(trader_seed)
    if side == "SELL_COL":
        taker_pays = {"currency": currency, "issuer": issuer_addr, "value": str(Decimal(iou_amt))}
        taker_gets = str(xrp_to_drops(float(xrp_amt)))
    else:  # BUY_COL
        taker_pays = str(xrp_to_drops(float(xrp_amt)))
        taker_gets = {"currency": currency, "issuer": issuer_addr, "value": str(Decimal(iou_amt))}

    tx = OfferCreate(account=w.classic_address, taker_gets=taker_gets, taker_pays=taker_pays)
    return sign_submit(tx, w, client)

def list_offers(client: JsonRpcClient, seed: str):
    addr = addr_from_seed(seed)
    return client.request(req.AccountOffers(account=addr)).result

def cancel_offer(client: JsonRpcClient, seed: str, seq: int):
    w = wallet_from_seed(seed)
    tx = OfferCancel(account=w.classic_address, offer_sequence=int(seq))
    return sign_submit(tx, w, client)

def orderbook_snapshot(client: JsonRpcClient, issuer_addr: str, currency: str, limit: int = 20):
    """
    Returns:
      - bids: makers BUYING COL (taker pays XRP, gets COL)
      - asks: makers SELLING COL (taker pays COL, gets XRP)
    """
    base = {"currency": currency, "issuer": issuer_addr}   # IOU side (COL)
    xrp  = XRPModel()                                      # XRP currency object
    neutral_taker = "rrrrrrrrrrrrrrrrrrrrBZbvji"

    # BIDS (makers buying COL): taker PAYS XRP, GETS COL
    bids = client.request(
        req.BookOffers(taker=neutral_taker, taker_pays=xrp, taker_gets=base, limit=limit)
    ).result.get("offers", [])

    # ASKS (makers selling COL): taker PAYS COL, GETS XRP
    asks = client.request(
        req.BookOffers(taker=neutral_taker, taker_pays=base, taker_gets=xrp, limit=limit)
    ).result.get("offers", [])

    def norm(o: Dict[str, Any], up: str, low: str):
        return o.get(low) if low in o else o.get(up)

    def shape(o: Dict[str, Any]):
        return {
            "seq":       norm(o, "Sequence", "seq"),
            "quality":   o.get("quality"),
            "TakerGets": norm(o, "TakerGets", "taker_gets"),
            "TakerPays": norm(o, "TakerPays", "taker_pays"),
        }

    return {"bids": [shape(o) for o in bids], "asks": [shape(o) for o in asks]}
