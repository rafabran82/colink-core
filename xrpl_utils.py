from __future__ import annotations

import contextlib
from decimal import Decimal
from typing import Any

from xrpl.clients import JsonRpcClient
from xrpl.models import requests as req
from xrpl.models.currencies import XRP as XRPModel
from xrpl.models.transactions import OfferCancel, OfferCreate, Payment, TrustSet
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet


def sign_submit(tx, wallet: Wallet, client: JsonRpcClient) -> dict[str, Any]:
    """
    Autofill + sign + reliable submit wrapper.
    Returns {"ok": True, "engine": <result>} on success or
            {"ok": False, "type": "...", "error": "...", "engine": <maybe>} on error.
    """
    try:
        filled = autofill(tx, client)
        signed = sign(filled, wallet)
        res = submit_and_wait(signed, client).result
        return {"ok": True, "engine": res}
    except Exception as e:
        # Keep it generic to avoid import churn across xrpl-py versions
        payload = None
        with contextlib.suppress(Exception):
            payload = getattr(e, "result", None)
        return {"ok": False, "type": e.__class__.__name__, "error": str(e), "engine": payload}


def client_from(url: str) -> JsonRpcClient:
    return JsonRpcClient(url)


def wallet_from_seed(seed: str) -> Wallet:
    # NOTE: will raise if invalid; callers should handle and convert to 400s
    return Wallet.from_seed(seed)


def addr_from_seed(seed: str) -> str:
    return wallet_from_seed(seed).classic_address


def get_xrp_balance(client: JsonRpcClient, address: str) -> int:
    r = client.request(req.AccountInfo(account=address, ledger_index="validated", strict=True))
    return int(r.result["account_data"]["Balance"])


def get_account_lines(client: JsonRpcClient, address: str) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    marker = None
    while True:
        r = client.request(req.AccountLines(account=address, ledger_index="validated", limit=400, marker=marker))
        lines.extend(r.result.get("lines", []))
        marker = r.result.get("marker")
        if not marker:
            break
    return lines


def fetch_col_state(client: JsonRpcClient, trader_seed: str, issuer_addr: str, currency: str) -> dict[str, Any]:
    trader_addr = addr_from_seed(trader_seed)
    ixrp = get_xrp_balance(client, issuer_addr)
    txrp = get_xrp_balance(client, trader_addr)
    lines = get_account_lines(client, trader_addr)
    ious = [line_ for line_ in lines if line_.get("account") == issuer_addr and line_.get("currency") == currency]
    return {
        "issuer": {"address": issuer_addr, "xrp_drops": ixrp},
        "trader": {"address": trader_addr, "xrp_drops": txrp, "ious": ious},
    }


def ensure_trustline(client: JsonRpcClient, trader_seed: str, issuer_addr: str, currency: str, limit: str) -> dict[str, Any]:
    try:
        w = wallet_from_seed(trader_seed)
    except Exception as e:
        return {"ok": False, "type": e.__class__.__name__, "error": f"Invalid trader seed: {e}", "engine": None}

    tx = TrustSet(
        account=w.classic_address,
        limit_amount={"currency": currency, "issuer": issuer_addr, "value": str(limit)},
    )
    return sign_submit(tx, w, client)


def iou_payment(client: JsonRpcClient, issuer_seed: str, dest: str, currency: str, amount: str) -> dict[str, Any]:
    try:
        w = wallet_from_seed(issuer_seed)
    except Exception as e:
        return {"ok": False, "type": e.__class__.__name__, "error": f"Invalid issuer seed: {e}", "engine": None}

    tx = Payment(
        account=w.classic_address,
        destination=dest,
        amount={"currency": currency, "issuer": w.classic_address, "value": str(amount)},
    )
    return sign_submit(tx, w, client)


def create_offer(
    client: JsonRpcClient,
    side: str,
    trader_seed: str,
    issuer_addr: str,
    currency: str,
    iou_amt: str,
    xrp_amt: str,
) -> dict[str, Any]:
    """
    SELL_COL: taker_pays = COL, taker_gets = XRP(drops)
    BUY_COL : taker_pays = XRP(drops), taker_gets = COL
    """
    try:
        w = wallet_from_seed(trader_seed)
    except Exception as e:
        return {"ok": False, "type": e.__class__.__name__, "error": f"Invalid trader seed: {e}", "engine": None}

    if side == "SELL_COL":
        taker_pays = {"currency": currency, "issuer": issuer_addr, "value": str(Decimal(iou_amt))}
        taker_gets = str(xrp_to_drops(float(xrp_amt)))
    else:
        taker_pays = str(xrp_to_drops(float(xrp_amt)))
        taker_gets = {"currency": currency, "issuer": issuer_addr, "value": str(Decimal(iou_amt))}

    tx = OfferCreate(account=w.classic_address, taker_gets=taker_gets, taker_pays=taker_pays)
    return sign_submit(tx, w, client)


def list_offers(client: JsonRpcClient, seed: str) -> dict[str, Any]:
    addr = addr_from_seed(seed)
    return client.request(req.AccountOffers(account=addr)).result


def cancel_offer(client: JsonRpcClient, seed: str, seq: int) -> dict[str, Any]:
    w = wallet_from_seed(seed)
    tx = OfferCancel(account=w.classic_address, offer_sequence=int(seq))
    return sign_submit(tx, w, client)


def orderbook_snapshot(client: JsonRpcClient, issuer_addr: str, currency: str, limit: int = 20) -> dict[str, Any]:
    """
    Returns:
      - bids: makers BUYING COL (taker pays XRP, gets COL)
      - asks: makers SELLING COL (taker pays COL, gets XRP)
    """
    base = {"currency": currency, "issuer": issuer_addr}
    xrp = XRPModel()
    neutral_taker = "rrrrrrrrrrrrrrrrrrrrBZbvji"

    bids = client.request(
        req.BookOffers(taker=neutral_taker, taker_pays=xrp, taker_gets=base, limit=limit)
    ).result.get("offers", [])

    asks = client.request(
        req.BookOffers(taker=neutral_taker, taker_pays=base, taker_gets=xrp, limit=limit)
    ).result.get("offers", [])

    def norm(o: dict[str, Any], up: str, low: str):
        return o.get(low) if low in o else o.get(up)

    def shape(o: dict[str, Any]):
        return {
            "seq":       norm(o, "Sequence", "seq"),
            "quality":   o.get("quality"),
            "TakerGets": norm(o, "TakerGets", "taker_gets"),
            "TakerPays": norm(o, "TakerPays", "taker_pays"),
        }

    return {"bids": [shape(o) for o in bids], "asks": [shape(o) for o in asks]}
