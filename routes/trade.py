import time
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import settings
from xrpl_utils import (
    client_from,
    create_offer,
    ensure_trustline,
    orderbook_snapshot,
)

router = APIRouter(prefix="", tags=["trade"])

# =========================
# Paper engine state
# =========================
PAPER_BOOK: dict[str, list[dict[str, Any]]] = {"bids": [], "asks": []}

# Running paper portfolio (COL against XRP)
PAPER_POSITION = {
    "col": Decimal("0"),
    "xrp": Decimal("0"),
    "avg_price": None,              # XRP per COL (Decimal or None)
    "realized_pnl_xrp": Decimal("0")
}

def _q(x: Decimal, places=6) -> str:
    return str(x.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP))

def _now_ts() -> int:
    return int(time.time())

def _record_fill_buy(amount_col: Decimal, price_xrp_per_col: Decimal) -> None:
    """Buy COL using XRP (paper)."""
    spend_xrp = amount_col * price_xrp_per_col
    prev_col = PAPER_POSITION["col"]
    prev_avg = PAPER_POSITION["avg_price"]

    # cash movement
    PAPER_POSITION["xrp"] -= spend_xrp

    # inventory + average cost
    new_col = prev_col + amount_col
    if prev_avg is None or prev_col == 0:
        PAPER_POSITION["avg_price"] = price_xrp_per_col
    else:
        PAPER_POSITION["avg_price"] = (prev_avg * prev_col + price_xrp_per_col * amount_col) / new_col

    PAPER_POSITION["col"] = new_col

def _record_fill_sell(amount_col: Decimal, price_xrp_per_col: Decimal) -> None:
    """Sell COL for XRP (paper)."""
    recv_xrp = amount_col * price_xrp_per_col
    prev_col = PAPER_POSITION["col"]
    prev_avg = PAPER_POSITION["avg_price"]

    # cash movement
    PAPER_POSITION["xrp"] += recv_xrp

    # realized PnL only if we had an average cost
    if prev_avg is not None and prev_col > 0:
        PAPER_POSITION["realized_pnl_xrp"] += (price_xrp_per_col - prev_avg) * amount_col

    # inventory update
    new_col = prev_col - amount_col
    PAPER_POSITION["col"] = new_col
    if new_col <= 0:
        PAPER_POSITION["avg_price"] = None
    # else keep the same avg_price for remaining inventory

# ---------- Models ----------
class SeedBookReq(BaseModel):
    mid_price_xrp_per_col: Decimal = Field(..., description="Target mid price in XRP per COL (e.g., 0.10)")
    steps: int = Field(2, description="Levels up and down (0 = only mid)")
    step_pct: Decimal = Field(Decimal("0.05"), description="Percentage gap per level (e.g., 0.05 = 5%)")
    base_size_col: Decimal = Field(Decimal("25"), description="COL size at mid; scales per level")
    size_scale: Decimal = Field(Decimal("1.00"), description="Multiply size each level")

class MarketReq(BaseModel):
    amount_col: Decimal = Field(..., gt=Decimal("0"))
    max_slippage_pct: Decimal = Field(Decimal("0.20"), description="Stop if best price worse than mid*(1+/-slippage)")
    limit: int = 20

# ---------- Helpers ----------
def _price_from_ask(ask: dict[str, Any]) -> Decimal:
    # ask: maker SELLING COL (TakerPays=COL, TakerGets=XRP drops)
    tg = ask["TakerGets"]  # drops as string
    tp = ask["TakerPays"]  # {currency, issuer, value}
    xrp = Decimal(tg) / Decimal(1_000_000)
    col = Decimal(str(tp["value"]))
    return (xrp / col)

def _price_from_bid(bid: dict[str, Any]) -> Decimal:
    # bid: maker BUYING COL (TakerGets=COL, TakerPays=XRP drops)
    tp = bid["TakerPays"]  # drops str
    tg = bid["TakerGets"]  # {currency, issuer, value}
    xrp = Decimal(tp) / Decimal(1_000_000)
    col = Decimal(str(tg["value"]))
    return (xrp / col)

def _maker_sell_col(client, iou_amt: Decimal, price_xrp_per_col: Decimal):
    if settings.paper_mode:
        # add ASKS level locally
        PAPER_BOOK["asks"].append({
            "TakerGets": str((price_xrp_per_col * iou_amt * Decimal(1_000_000)).quantize(Decimal("1"))),  # XRP drops
            "TakerPays": {"currency": settings.col_code, "issuer": settings.issuer_addr or "PAPER", "value": _q(iou_amt, 6)},
            "quality": _q((price_xrp_per_col * Decimal(1_000_000)), 0),
            "seq": 0
        })
        return {"ok": True, "engine": {"mode": "paper", "side": "SELL_COL", "price_xrp_per_col": _q(price_xrp_per_col, 4), "iou_amt": str(iou_amt), "txid": f"PAPER-SELL_COL-{_now_ts()}", "ledger_index": 0}}

    # XRPL path
    res = create_offer(
        client=client,
        side="SELL_COL",
        trader_seed=settings.trader_seed,
        issuer_addr=settings.issuer_addr,
        currency=settings.col_code,
        iou_amt=str(iou_amt),
        xrp_amt=str(iou_amt * price_xrp_per_col),
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail={"action": "SELL_COL", **res})
    return res

def _maker_buy_col(client, iou_amt: Decimal, price_xrp_per_col: Decimal):
    if settings.paper_mode:
        # add BIDS level locally
        PAPER_BOOK["bids"].append({
            "TakerPays": str((price_xrp_per_col * iou_amt * Decimal(1_000_000)).quantize(Decimal("1"))),  # XRP drops
            "TakerGets": {"currency": settings.col_code, "issuer": settings.issuer_addr or "PAPER", "value": _q(iou_amt, 6)},
            "quality": _q((price_xrp_per_col * Decimal(1_000_000)), 0),
            "seq": 0
        })
        return {"ok": True, "engine": {"mode": "paper", "side": "BUY_COL", "price_xrp_per_col": _q(price_xrp_per_col, 4), "iou_amt": str(iou_amt), "txid": f"PAPER-BUY_COL-{_now_ts()}", "ledger_index": 0}}

    # XRPL path
    res = create_offer(
        client=client,
        side="BUY_COL",
        trader_seed=settings.trader_seed,
        issuer_addr=settings.issuer_addr,
        currency=settings.col_code,
        iou_amt=str(iou_amt),
        xrp_amt=str(iou_amt * price_xrp_per_col),
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail={"action": "BUY_COL", **res})
    return res

def _preflight_or_400():
    # Ensure we have usable params before signing any tx (only enforced in non-paper mode)
    if settings.paper_mode:
        return
    errs = {}
    if not settings.issuer_addr:
        errs["issuer_addr"] = "missing_or_invalid"
    if not settings.trader_addr:
        errs["trader_addr"] = "missing_or_invalid"
    if settings.issuer_seed and settings.issuer_seed_error:
        errs["issuer_seed_error"] = settings.issuer_seed_error
    if settings.trader_seed and settings.trader_seed_error:
        errs["trader_seed_error"] = settings.trader_seed_error
    if errs:
        raise HTTPException(status_code=400, detail={"error": "preflight_failed", **errs})

# ---------- Routes ----------
@router.post("/seed-book")
def seed_book(req: SeedBookReq):
    """Create a symmetric ladder around mid_price with `steps` levels (including mid)."""
    _preflight_or_400()
    client = client_from(settings.rpc_url)

    # make sure trustline exists (no-op if already present) unless in paper mode
    if not settings.paper_mode:
        tl = ensure_trustline(client, settings.trader_seed, settings.issuer_addr, settings.col_code, limit=str(10_000_000))
        if not tl.get("ok"):
            raise HTTPException(status_code=400, detail={"action": "TRUSTLINE", **tl})

    results = {"asks": [], "bids": []}
    size0 = Decimal(req.base_size_col)

    for i in range(req.steps + 1):
        size_i = (size0 * (req.size_scale ** i))
        ask_px = (req.mid_price_xrp_per_col * (Decimal(1) + req.step_pct * i))
        bid_px = (req.mid_price_xrp_per_col * (Decimal(1) - req.step_pct * i))

        results["asks"].append({"level": i, "size_col": str(size_i), "price": str(ask_px), "engine": _maker_sell_col(client, size_i, ask_px)})
        results["bids"].append({"level": i, "size_col": str(size_i), "price": str(bid_px), "engine": _maker_buy_col(client, size_i, bid_px)})

    return results

@router.post("/market-buy")
def market_buy(req: MarketReq):
    _preflight_or_400()
    client = client_from(settings.rpc_url)

    if settings.paper_mode:
        # Fill against best ask in-memory
        asks = sorted(PAPER_BOOK["asks"], key=_price_from_ask)
        if not asks:
            raise HTTPException(status_code=400, detail="No asks available to buy from.")
        to_buy = Decimal(req.amount_col)
        fills = []
        for a in list(asks):
            if to_buy <= 0:
                break
            price = _price_from_ask(a)
            avail_col = Decimal(str(a["TakerPays"]["value"]))
            take = min(avail_col, to_buy)
            # reduce/consume ask
            new_avail = avail_col - take
            if new_avail <= 0:
                PAPER_BOOK["asks"].remove(a)
            else:
                a["TakerPays"]["value"] = _q(new_avail, 6)
            _record_fill_buy(take, price)
            fills.append({"take_col": str(take), "price_xrp_per_col": str(price), "engine": {"ok": True, "engine": {"mode": "paper", "side": "FILL", "txid": f"PAPER-FILL-{_now_ts()}"}}})
            to_buy -= take
        if to_buy > 0:
            return {"status": "partial", "filled_entries": fills, "remaining_col": str(to_buy)}
        return {"status": "ok", "filled_entries": fills}

    # XRPL path (snapshot + place IOC-like offers)
    ob = orderbook_snapshot(client, settings.issuer_addr, settings.col_code, limit=req.limit)
    asks: list[dict[str, Any]] = ob.get("asks", [])
    if not asks:
        raise HTTPException(status_code=400, detail="No asks available to buy from.")

    bids: list[dict[str, Any]] = ob.get("bids", [])
    if bids:
        best_bid = _price_from_bid(bids[0])
        best_ask = _price_from_ask(asks[0])
        mid = (best_bid + best_ask) / Decimal(2)
        max_ok = mid * (Decimal(1) + req.max_slippage_pct)
        if best_ask > max_ok:
            raise HTTPException(status_code=400, detail=f"Best ask {best_ask} worse than slippage cap {max_ok}")

    to_buy = Decimal(req.amount_col)
    fills = []
    for a in asks:
        if to_buy <= 0:
            break
        price = _price_from_ask(a)
        avail_col = Decimal(str(a["TakerPays"]["value"]))
        take = min(avail_col, to_buy)
        resp = _maker_buy_col(client, take, price)
        fills.append({"take_col": str(take), "price_xrp_per_col": str(price), "engine": resp})
        to_buy -= take

    if to_buy > 0:
        return {"status": "partial", "filled_entries": fills, "remaining_col": str(to_buy)}
    return {"status": "ok", "filled_entries": fills}

@router.post("/market-sell")
def market_sell(req: MarketReq):
    _preflight_or_400()
    client = client_from(settings.rpc_url)

    if settings.paper_mode:
        # Fill against best bid in-memory
        bids = sorted(PAPER_BOOK["bids"], key=_price_from_bid, reverse=True)
        if not bids:
            raise HTTPException(status_code=400, detail="No bids available to sell into.")
        to_sell = Decimal(req.amount_col)
        fills = []
        for b in list(bids):
            if to_sell <= 0:
                break
            price = _price_from_bid(b)
            avail_col = Decimal(str(b["TakerGets"]["value"]))
            take = min(avail_col, to_sell)
            # reduce/consume bid
            new_avail = avail_col - take
            if new_avail <= 0:
                PAPER_BOOK["bids"].remove(b)
            else:
                b["TakerGets"]["value"] = _q(new_avail, 6)
            _record_fill_sell(take, price)
            fills.append({"take_col": str(take), "price_xrp_per_col": str(price), "engine": {"ok": True, "engine": {"mode": "paper", "side": "FILL", "txid": f"PAPER-FILL-{_now_ts()}"}}})
            to_sell -= take
        if to_sell > 0:
            return {"status": "partial", "filled_entries": fills, "remaining_col": str(to_sell)}
        return {"status": "ok", "filled_entries": fills}

    # XRPL path
    ob = orderbook_snapshot(client, settings.issuer_addr, settings.col_code, limit=req.limit)
    bids: list[dict[str, Any]] = ob.get("bids", [])
    if not bids:
        raise HTTPException(status_code=400, detail="No bids available to sell into.")

    asks: list[dict[str, Any]] = ob.get("asks", [])
    if asks:
        best_bid = _price_from_bid(bids[0])
        best_ask = _price_from_ask(asks[0])
        mid = (best_bid + best_ask) / Decimal(2)
        min_ok = mid * (Decimal(1) - req.max_slippage_pct)
        if best_bid < min_ok:
            raise HTTPException(status_code=400, detail=f"Best bid {best_bid} worse than slippage floor {min_ok}")

    to_sell = Decimal(req.amount_col)
    fills = []
    for b in bids:
        if to_sell <= 0:
            break
        price = _price_from_bid(b)
        avail_col = Decimal(str(b["TakerGets"]["value"]))
        take = min(avail_col, to_sell)
        resp = _maker_sell_col(client, take, price)
        fills.append({"take_col": str(take), "price_xrp_per_col": str(price), "engine": resp})
        to_sell -= take

    if to_sell > 0:
        return {"status": "partial", "filled_entries": fills, "remaining_col": str(to_sell)}
    return {"status": "ok", "filled_entries": fills}


