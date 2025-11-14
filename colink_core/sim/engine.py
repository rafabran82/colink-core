from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class PoolState:
    copx_reserve: float
    col_reserve: float
    mid_price: float
    spread: float
    ledger_index: Optional[int] = None
    offer_count: Optional[int] = None


def parse_reserves_from_balances(snapshot):
    """
    Extract real COPX and COL reserves from LP IOU balances.
    """
    lp = snapshot.balances.lp
    copx = 0.0
    col = 0.0

    try:
        for entry in lp.ious or []:
            currency = entry.currency
            bal = float(entry.balance or 0.0)

            if currency == "CPX":
                copx = bal
            elif currency == "COL":
                col = bal
    except Exception:
        pass

    return copx, col


def parse_midprice_and_spread(snapshot):
    """
    Derive midprice and spread from orderbook if available.
    If no usable offers exist, defaults to (1.0, 0.0).
    """
    if not snapshot.orderbook or not snapshot.orderbook.offers:
        return 1.0, 0.0

    qualities = [o.quality for o in snapshot.orderbook.offers if o.quality]
    if not qualities:
        return 1.0, 0.0

    mid = min(qualities)
    # placeholder until we compute real spread
    return mid, 0.0


def extract_pool_from_snapshot(snapshot):
    """
    Build PoolState using real reserves + orderbook midprice.
    """
    copx, col = parse_reserves_from_balances(snapshot)
    mid, spr = parse_midprice_and_spread(snapshot)

    return PoolState(
        copx_reserve=copx,
        col_reserve=col,
        mid_price=mid,
        spread=spr,
        ledger_index=getattr(snapshot.orderbook, "ledger_index", None),
        offer_count=len(snapshot.orderbook.offers)
        if snapshot.orderbook else None,
    )




    k = x * y

    if direction == "CPX->COL":
        new_x = x + amount_in
        new_y = k / new_x
        amount_out = y - new_y
        return {
            "ok": True,
            "in": amount_in,
            "out": amount_out,
            "new_copx": new_x,
            "new_col": new_y,
        }

    elif direction == "COL->CPX":
        new_y = y + amount_in
        new_x = k / new_y
        amount_out = x - new_x
        return {
            "ok": True,
            "in": amount_in,
            "out": amount_out,
            "new_copx": new_x,
            "new_col": new_y,
        }

    else:
        return {"ok": False, "error": "invalid direction"}

def simulate_swap(pool: PoolState, amount_in: float, direction: str) -> dict:
    """
    Constant-product AMM (x * y = k) baseline swap.
    direction = "CPX->COL" or "COL->CPX"
    """
    x = pool.copx_reserve
    y = pool.col_reserve

    if amount_in <= 0:
        return {"ok": False, "error": "amount_in must be > 0"}

    k = x * y

    if direction == "CPX->COL":
        new_x = x + amount_in
        new_y = k / new_x
        amount_out = y - new_y
        return {
            "ok": True,
            "in": amount_in,
            "out": amount_out,
            "new_copx": new_x,
            "new_col": new_y,
        }

    elif direction == "COL->CPX":
        new_y = y + amount_in
        new_x = k / new_y
        amount_out = x - new_x
        return {
            "ok": True,
            "in": amount_in,
            "out": amount_out,
            "new_copx": new_x,
            "new_col": new_y,
        }

    else:
        return {"ok": False, "error": "invalid direction"}

def run_sim(ctx):
    """
    Main XRPL-backed simulation entry point.
    Uses ctx.xrpl_snapshot to build a pool.
    """
    ps = extract_pool_from_snapshot(ctx.xrpl_snapshot)

    # Execute swap if swap inputs provided
    if getattr(ctx, "swap_direction", None) and getattr(ctx, "swap_amount", None):
        return simulate_swap(ps, ctx.swap_amount, ctx.swap_direction)

    return type("Result", (), {
        "ok": True,
        "msg": (
            f"pool={ps.copx_reserve}/{ps.col_reserve} "
            f"mid={ps.mid_price} spread={ps.spread}"
        ),
    })()





