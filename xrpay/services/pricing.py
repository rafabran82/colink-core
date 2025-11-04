from dataclasses import dataclass
from decimal import Decimal

@dataclass
class QuoteRequest:
    base: str
    quote: str
    side: str   # "BUY" or "SELL"
    amount: str
    slippageBps: int = 50

class PricingEngine:
    def __init__(self, provider):
        self.provider = provider

    async def quote(self, req: QuoteRequest | dict):
        if isinstance(req, dict):
            req = QuoteRequest(**req)
        data = await self.provider.get_quote(
            base=req.base,
            quote=req.quote,
            side=req.side,
            amount=req.amount,
            slippageBps=req.slippageBps
        )
        return data

