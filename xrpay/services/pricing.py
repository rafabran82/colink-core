from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

class SimProvider:
    """
    Minimal pricing simulation provider.
    """
    def get_quote(
        self,
        base: str,
        quote: str,
        side: str,
        amount: Decimal,
        *,
        slippage_bps: int = 25,
        **kwargs,  # tolerate extras like slippageBps
    ) -> dict:
        # normalize basics
        base_u = (base or "").upper()
        quote_u = (quote or "").upper()
        side_u = (side or "").upper()

        amt = Decimal(str(amount))

        # allow camelCase argument too
        if "slippageBps" in kwargs and kwargs.get("slippageBps") is not None:
            try:
                slippage_bps = int(kwargs["slippageBps"])
            except Exception:
                pass

        # simple deterministic mid for demo
        if base_u == "XRP" and quote_u == "USD":
            mid = Decimal("0.60")
        else:
            mid = Decimal("1.00")

        # impact derived from slippage basis points
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

# New-style singleton used by newer code
provider = SimProvider()

# ---- Backward-compat aliases / shims ----
class PricingEngine(SimProvider):
    """
    Compat alias allowing legacy imports like:
        from xrpay.services.pricing import PricingEngine
        engine = PricingEngine(_provider)
        await engine.quote(payload)
    """
    def __init__(self, *args, **kwargs):
        # ignore injected provider for the sim
        super().__init__()

    async def quote(self, payload: dict) -> dict:
        """
        Async facade expected by main.py: takes a dict payload and returns a dict.
        """
        base  = payload.get("base")
        quote = payload.get("quote")
        side  = payload.get("side", "BUY")
        # accept string/number; default 0 if missing
        amount = Decimal(str(payload.get("amount", "0")))

        # support both slippage_bps and slippageBps
        slippage = payload.get("slippage_bps")
        if slippage is None:
            slippage = payload.get("slippageBps")
        if slippage is None:
            slippage = 25
        try:
            slippage = int(slippage)
        except Exception:
            slippage = 25

        data = self.get_quote(
            base=base,
            quote=quote,
            side=side,
            amount=amount,
            slippage_bps=slippage,
        )

        # normalize key names to what routes expect (expiresAt camelCase)
        return {
            "price": data.get("price"),
            "fee_bps": data.get("fee_bps"),
            "impact_bps": data.get("impact_bps"),
            "expiresAt": data.get("expires_at") or data.get("expiresAt"),
        }

# Some code may import `pricing_engine`
pricing_engine = provider
