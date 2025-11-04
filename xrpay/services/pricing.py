from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

# --- Primary sim provider used by routes ---
class SimProvider:
    def get_quote(
        self,
        base: str,
        quote: str,
        side: str,
        amount: Decimal,
        *,
        slippage_bps: int = 25,
    ) -> dict:
        base_u = (base or "").upper()
        quote_u = (quote or "").upper()
        side_u = (side or "").upper()
        amt = Decimal(str(amount))

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

# singleton used by new code
provider = SimProvider()

# ---- Backward-compat aliases so old imports keep working ----
class PricingEngine(SimProvider):
    """Compat alias for older code that did `from xrpay.services.pricing import PricingEngine` and then `PricingEngine()`."""
    pass

# some code may import `pricing_engine` directly
pricing_engine = provider
