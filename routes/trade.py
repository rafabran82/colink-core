from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal, ROUND_DOWN
from typing import List, Dict, Any
import time

from config import settings
from xrpl_utils import (
    client_from,
    create_offer,
    orderbook_snapshot,
    ensure_trustline,
)

router = APIRouter(prefix="", tags=["trade"])

# -------- In-memory book for PAPER MODE --------
PAPER_BOOK = {"bids": [], "asks": []}  # same shape as xrpl_utils.orderbook_snapshot()

def _drops(amount_xrp: Decimal) -> str:
    # round down to integer drops
    drops = (amount_xrp * Decimal(1_000_000)).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return str(drops)

def _mk_ask_row(size_col: Decimal, price: Decimal, issuer_addr: str, currency: str) -> Dict[str, Any]:
    # ask: maker SELLING COL => taker_pays=COL, taker_gets=XRP(drops)
    return {
        "seq": int(time.time()),
        "quality": str((_drops(price) if price else "0")),
        "TakerGets": _drops(size_col * price),  # XRP in drops
        "TakerPays": {"currency": currency, "issuer": issuer_addr, "value": str(size_col)},
    }

def _mk_bid_row(size_col: Decimal, price: Decimal, issuer_addr: str, currency: str) -> Dict[str, Any]:
    # bid: maker BUYING COL => taker_pays=XRP(drops), taker_gets=COL
    return {
        "seq": int(time.time()),
        "quality": str((_drops(price) if price else "0")),
        "TakerPays": _drops(size_col * price),  # XRP in drops
        "TakerGets": {"currency": currency, "issuer": issuer_addr, "value": str(size_col)},
    }

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
def _price_from_ask(ask: Dict[str, Any]) -> Decimal:
    xrp = Decimal(ask["TakerGets"]) / Decimal(1_000_000)
    col = Decimal(str(ask["TakerPays"]["value"]))
    return (xrp / col)

def _price_from_bid(bid: Dict[str, Any]) -> Decimal:
    xrp = Decimal(bid["TakerPays"]) / Decimal(1_000_000)
    col = Decimal(str(bid["TakerGets"]["value"]))
    return (xrp / col)

def _paper_engine(side: str, iou_amt: Decimal, price: Decimal) -> Dict[str, Any]:
    now = int(time.time())
    return {"ok": True, "engine": {"mode": "paper", "side": side, "price_xrp_per_col": str(price),
                                   "iou_amt": str(iou_amt), "txid": f"PAPER-{side}-{now}", "ledger_index": 0}}

def _maker_sell_col(client, iou_amt: Decimal, price_xrp_per_col: Decimal):
    if settings.paper_mode:
        # add to ASK side
        PAPER_BOOK["asks"].append(_mk_ask_row(iou_amt, price_xrp_per_col, settings.issuer_addr, settings.col_code))
        return _paper_engine("SELL_COL", iou_amt, price_xrp_per_col)
    res = create_offer(client=client, side="SELL_COL", trader_seed=settings.trader_seed,
                       issuer_addr=settings.issuer_addr, currency=settings.col_code,
                       iou_amt=str(iou_amt), xrp_amt=str(iou_amt * price_xrp_per_col))
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail={"action": "SELL_COL", **res})
    return res

def _maker_buy_col(client, iou_amt: Decimal, price_xrp_per_col: Decimal):
    if settings.paper_mode:
        # add to BID side
        PAPER_BOOK["bids"].append(_mk_bid_row(iou_amt, price_xrp_per_col, settings.issuer_addr, settings.col_code))
        return _paper_engine("BUY_COL", iou_amt, price_xrp_per_col)
    res = create_offer(client=client, side="BUY_COL", trader_seed=settings.trader_seed,
                       issuer_addr=settings.issuer_addr, currency=settings.col_code,
                       iou_amt=str(iou_amt), xrp_amt=str(iou_amt * price_xrp_per_col))
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail={"action": "BUY_COL", **res})
    return res

def _preflight_or_400():
    if settings.paper_mode:
        if not settings.issuer_addr or not settings.trader_addr:
            raise HTTPException(status_code=400, detail={"error": "preflight_failed", "need": "issuer_addr & trader_addr"})
        return
    # real mode
    errs = {}
    if not settings.issuer_addr: errs["issuer_addr"] = "missing_or_invalid"
    if not settings.trader_addr: errs["trader_addr"] = "missing_or_invalid"
    if settings.issuer_seed and settings.issuer_seed_error: errs["issuer_seed_error"] = settings.issuer_seed_error
    if settings.trader_seed and settings.trader_seed_error: errs["trader_seed_error"] = settings.trader_seed_error
    if errs: raise HTTPException(status_code=400, detail={"error": "preflight_failed", **errs})

# ---------- Routes ----------
@router.post("/seed-book")
def seed_book(req: SeedBookReq):
    """Create a symmetric ladder around mid_price with `steps` levels (including mid)."""
    _preflight_or_400()
    client = client_from(settings.rpc_url)

    # clear paper book each time you seed
    if settings.paper_mode:
        PAPER_BOOK["bids"].clear()
        PAPER_BOOK["asks"].clear()

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
        results["asks"].append({"level": i, "size_col": str(size_i), "price": str(ask_px),
                                "engine": _maker_sell_col(client, size_i, ask_px)})
        results["bids"].append({"level": i, "size_col": str(size_i), "price": str(bid_px),
                                "engine": _maker_buy_col(client, size_i, bid_px)})

    return results

def _consume_from(side_rows: List[Dict[str, Any]], needed_col: Decimal, price_fn):
    """Match from best price first: for asks, lower price is better; for bids, higher price is better."""
    # sort by price: asks ↑, bids ↓ decided by caller
    fills = []
    remaining = Decimal(needed_col)
    i = 0
    while i < len(side_rows) and remaining > 0:
        row = side_rows[i]
        price = price_fn(row)
        avail = Decimal(str(row["TakerPays"]["value"])) if "TakerPays" in row and isinstance(row["TakerPays"], dict) else Decimal(str(row["TakerGets"]["value"]))
        take = min(avail, remaining)

        # reduce row
        new_avail = avail - take
        if "TakerPays" in row and isinstance(row["TakerPays"], dict):
            # ask row (COL on TakerPays)
            row["TakerPays"]["value"] = str(new_avail)
            row["TakerGets"] = _drops(Decimal(row["TakerPays"]["value"]) * price)
        else:
            # bid row (COL on TakerGets)
            row["TakerGets"]["value"] = str(new_avail)
            row["TakerPays"] = _drops(Decimal(row["TakerGets"]["value"]) * price)

        fills.append({"take_col": str(take), "price_xrp_per_col": str(price),
                      "engine": {"ok": True, "engine": {"mode": "paper", "side": "FILL", "txid": f"PAPER-FILL-{int(time.time())}"}}})

        if new_avail <= 0:
            side_rows.pop(i)
        else:
            i += 1
        remaining -= take

    status = "ok" if remaining <= 0 else "partial"
    return status, fills, remaining

@router.post("/market-buy")
def market_buy(req: MarketReq):
    _preflight_or_400()
    client = client_from(settings.rpc_url)

    # choose orderbook source
    if settings.paper_mode:
        asks = sorted(PAPER_BOOK["asks"], key=_price_from_ask)  # best price first
        bids = sorted(PAPER_BOOK["bids"], key=_price_from_bid, reverse=True)
    else:
        ob = orderbook_snapshot(client, settings.issuer_addr, settings.col_code, limit=req.limit)
        asks = ob.get("asks", [])
        bids = ob.get("bids", [])

    if not asks:
        raise HTTPException(status_code=400, detail="No asks available to buy from.")

    if bids:
        best_bid = _price_from_bid(bids[0])
        best_ask = _price_from_ask(asks[0])
        mid = (best_bid + best_ask) / Decimal(2)
        max_ok = mid * (Decimal(1) + req.max_slippage_pct)
        if best_ask > max_ok:
            raise HTTPException(status_code=400, detail=f"Best ask {best_ask} worse than slippage cap {max_ok}")

    if settings.paper_mode:
        status, fills, remaining = _consume_from(asks, Decimal(req.amount_col), _price_from_ask)
        if status == "partial":
            return {"status": "partial", "filled_entries": fills, "remaining_col": str(remaining)}
        return {"status": "ok", "filled_entries": fills}

    # real mode: place crossing offers (omitted for brevity; you already had it)
    raise HTTPException(status_code=400, detail="Market crossing in real mode not implemented here.")

@router.post("/market-sell")
def market_sell(req: MarketReq):
    _preflight_or_400()
    client = client_from(settings.rpc_url)

    if settings.paper_mode:
        bids = sorted(PAPER_BOOK["bids"], key=_price_from_bid, reverse=True)
        asks = sorted(PAPER_BOOK["asks"], key=_price_from_ask)
    else:
        ob = orderbook_snapshot(client, settings.issuer_addr, settings.col_code, limit=req.limit)
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])

    if not bids:
        raise HTTPException(status_code=400, detail="No bids available to sell into.")

    if asks:
        best_bid = _price_from_bid(bids[0])
        best_ask = _price_from_ask(asks[0])
        mid = (best_bid + best_ask) / Decimal(2)
        min_ok = mid * (Decimal(1) - req.max_slippage_pct)
        if best_bid < min_ok:
            raise HTTPException(status_code=400, detail=f"Best bid {best_bid} worse than slippage floor {min_ok}")

    if settings.paper_mode:
        status, fills, remaining = _consume_from(bids, Decimal(req.amount_col), _price_from_bid)
        if status == "partial":
            return {"status": "partial", "filled_entries": fills, "remaining_col": str(remaining)}
        return {"status": "ok", "filled_entries": fills}

    raise HTTPException(status_code=400, detail="Market crossing in real mode not implemented here.")
