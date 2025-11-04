from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

class SimProvider:
    def get_quote(
        self,
        base: str,
        quote: str,
        side: str,
        amount: Decimal,
        *,
        slippage_bps: int = 25,
        **kwargs,  # accept extras like slippageBps for backward compat
    ) -> dict:
        # normalize inputs
        base_u = (base or "").upper()
        quote_u = (quote or "").upper()
        side_u = (side or "").upper()
        amt = Decimal(str(amount))

        # allow camelCase arg name too
        if "slippageBps" in kwargs and kwargs.get("slippageBps") is not None:
            try:
                slippage_bps = int(kwargs["slippageBps"])
            except Exception:
                pass

        # simple deterministic mid
        if base_u == "XRP" and quote_u == "USD":
            mid = Decimal("0.60")
        else:
            mid = Decimal("1.00")

        impact = Decimal(slippage_bps) / Decimal(10_000)

        if side_u == "BUY":
            px = mid * (Decimal(1) + impact / Decimal(2))
        else:
            px = mid * (Decimal(1) - impact / Decimal(2))

        fee_bps = 25
        expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())

        return {
            "price": float(px),
            "fee_bps": int(fee_bps),
            "impact_bps": int(slippage_bps),
            "expires_at": expires_at,
        }

# singleton for new code
provider = SimProvider()

# ---- Backward-compat aliases ----
class PricingEngine(SimProvider):
    """Compat alias allowing old code to do PricingEngine(_provider)."""
    def __init__(self, *args, **kwargs):
        # ignore any injected provider; we don't need it for the sim
        super().__init__()

# some code may import `pricing_engine`
pricing_engine = provider
