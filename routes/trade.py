from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Dict, Any

from config import settings
from xrpl_utils import (
    client_from,
    create_offer,
    orderbook_snapshot,
    ensure_trustline,
)

router = APIRouter(prefix="", tags=["trade"])

# ---------- Models ----------
class SeedBookReq(BaseModel):
    mid_price_xrp_per_col: Decimal = Field(..., description="Target mid price in XRP per COL (e.g., 0.10)")
    steps: int = Field(2, description="Levels up and down")
    step_pct: Decimal = Field(Decimal("0.05"), description="Percentage gap per level (e.g., 0.05 = 5%)")
    base_size_col: Decimal = Field(Decimal("25"), description="COL size at mid; scales per level")
    size_scale: Decimal = Field(Decimal("1.00"), description="Multiply size each level")

class MarketReq(BaseModel):
    amount_col: Decimal = Field(..., gt=Decimal("0"))
    max_slippage_pct: Decimal = Field(Decimal("0.20"), description="Stop if best price worse than mid*(1+/-slippage)")
    limit: int = 20

# ---------- Helpers ----------
def _price_from_ask(ask: Dict[str, Any]) -> Decimal:
    # ask: maker SELLING COL (TakerPays=COL, TakerGets=XRP drops)
    tg = ask["TakerGets"]  # drops as string
    tp = ask["TakerPays"]  # {currency, issuer, value}
    xrp = Decimal(tg) / Decimal(1_000_000)
    col = Decimal(str(tp["value"]))
    return (xrp / col)

def _price_from_bid(bid: Dict[str, Any]) -> Decimal:
    # bid: maker BUYING COL (TakerGets=COL, TakerPays=XRP drops)
    tp = bid["TakerPays"]  # drops str
    tg = bid["TakerGets"]  # {currency, issuer, value}
    xrp = Decimal(tp) / Decimal(1_000_000)
    col = Decimal(str(tg["value"]))
    return (xrp / col)

def _maker_sell_col(client, iou_amt: Decimal, price_xrp_per_col: Decimal):
    # SELL_COL: taker_pays=COL, taker_gets=XRP(drops)
    res = create_offer(
        client=client,
        side="SELL_COL",
        trader_seed=settings.TRADER_SEED,
        issuer_addr=settings.ISSUER_ADDR,
        currency=settings.COL_CODE,
        iou_amt=str(iou_amt),
        xrp_amt=str(iou_amt * price_xrp_per_col),
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail={"action": "SELL_COL", **res})
    return res

def _maker_buy_col(client, iou_amt: Decimal, price_xrp_per_col: Decimal):
    # BUY_COL: taker_pays=XRP, taker_gets=COL
    res = create_offer(
        client=client,
        side="BUY_COL",
        trader_seed=settings.TRADER_SEED,
        issuer_addr=settings.ISSUER_ADDR,
        currency=settings.COL_CODE,
        iou_amt=str(iou_amt),
        xrp_amt=str(iou_amt * price_xrp_per_col),
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail={"action": "BUY_COL", **res})
    return res

# ---------- Routes ----------
@router.post("/seed-book")
def seed_book(req: SeedBookReq):
    """
    Create a symmetric ladder around mid_price with `steps` levels (including mid).
    """
    client = client_from(settings.RPC_URL)
    tl = ensure_trustline(client, settings.TRADER_SEED, settings.ISSUER_ADDR, settings.COL_CODE, limit=str(10_000_000))
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
    client = client_from(settings.RPC_URL)
    ob = orderbook_snapshot(client, settings.ISSUER_ADDR, settings.COL_CODE, limit=req.limit)

    asks: List[Dict[str, Any]] = ob.get("asks", [])
    if not asks:
        raise HTTPException(status_code=400, detail="No asks available to buy from.")

    bids: List[Dict[str, Any]] = ob.get("bids", [])
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
    client = client_from(settings.RPC_URL)
    ob = orderbook_snapshot(client, settings.ISSUER_ADDR, settings.COL_CODE, limit=req.limit)

    bids: List[Dict[str, Any]] = ob.get("bids", [])
    if not bids:
        raise HTTPException(status_code=400, detail="No bids available to sell into.")

    asks: List[Dict[str, Any]] = ob.get("asks", [])
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
