from __future__ import annotations
from typing import Dict, Any
import time

class PricingEngine:
    def __init__(self, provider):
        self.provider = provider

    async def quote(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # expects base, quote, side, amount, slippageBps
        q = await self.provider.get_quote(
            base=payload["base"],
            quote=payload["quote"],
            side=payload.get("side","BUY"),
            amount=payload["amount"],
            slippage_bps=int(payload.get("slippageBps", 25))
        )
        return {
            "price": q["price"],
            "fee_bps": q["fee_bps"],
            "impact_bps": q["impact_bps"],
            "expiresAt": int(time.time()) + 30
        }
