from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Simple deterministic pricing sim for test/dev
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

        # Mid prices for a couple of pairs; default to 1.00 if unknown
        if base_u == "XRP" and quote_u == "USD":
            mid = Decimal("0.60")
        else:
            mid = Decimal("1.00")

        # Turn bps into a fractional impact (50 bps = 0.005)
        impact = Decimal(slippage_bps) / Decimal(10_000)

        # Simple half-spread around mid based on side
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


# Export a singleton for easy import
provider = SimProvider()
