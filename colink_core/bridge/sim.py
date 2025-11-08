from __future__ import annotations
import dataclasses as dc
import math
import random
from typing import Tuple

@dc.dataclass
class Pool:
    """Constant-product AMM pool x*y=k with fee in bps."""
    base: str
    quote: str
    x: float
    y: float
    fee_bps: float = 30.0  # 0.30%

    def price_quote_per_base(self) -> float:
        return self.y / max(self.x, 1e-12)

    def swap_out(self, amount_in: float, base_to_quote: bool) -> Tuple[float, float]:
        """
        Return (amount_out, fee_paid). Updates reserves in-place.
        base_to_quote=True → input BASE receive QUOTE.
        """
        if amount_in <= 0:
            return 0.0, 0.0

        fee = amount_in * (self.fee_bps / 10_000.0)
        ain = amount_in - fee

        if base_to_quote:
            # add to base, remove from quote
            k = self.x * self.y
            x_new = self.x + ain
            y_new = k / max(x_new, 1e-12)
            aout = max(self.y - y_new, 0.0)
            self.x, self.y = x_new, y_new
            return aout, fee
        else:
            # add to quote, remove from base
            k = self.x * self.y
            y_new = self.y + ain
            x_new = k / max(y_new, 1e-12)
            aout = max(self.x - x_new, 0.0)
            self.x, self.y = x_new, y_new
            return aout, fee

@dc.dataclass
class BridgeRoute:
    """Two-hop route: A -> M -> B (e.g., COL -> COPX -> XRP)."""
    hop1: Pool
    hop2: Pool
    a: str
    m: str
    b: str

class BridgeSim:
    def __init__(self, seed: int = 777):
        self.rnd = random.Random(seed)

    def simulate(self, route: BridgeRoute, amount_in: float) -> dict:
        """
        Perform A->M then M->B swaps; return detailed result with slippage & fees.
        """
        # mid prices at start
        p1_0 = route.hop1.price_quote_per_base()   # M per A
        p2_0 = route.hop2.price_quote_per_base()   # B per M

        # Hop 1: A -> M
        out_m, fee1 = route.hop1.swap_out(amount_in, base_to_quote=True)

        # Hop 2: M -> B
        out_b, fee2 = route.hop2.swap_out(out_m, base_to_quote=True)

        total_fees = fee1 + fee2
        effective_ab = out_b / max(amount_in, 1e-12)
        ideal_ab = p1_0 * p2_0
        slippage_bps = 0.0
        if ideal_ab > 0:
            slippage_bps = max(0.0, (ideal_ab - effective_ab) / ideal_ab * 10_000.0)

        return {
            "route": [route.a, route.m, route.b],
            "amount_in": amount_in,
            "amount_mid": out_m,
            "amount_out": out_b,
            "fees_total": total_fees,
            "mid_price_initial": {
                f"{route.a}/{route.m}": p1_0,
                f"{route.m}/{route.b}": p2_0,
            },
            "effective_price_ab": effective_ab,
            "ideal_price_ab": ideal_ab,
            "slippage_bps": slippage_bps,
            "success": True,
            "p95_latency_ms": None,
        }
