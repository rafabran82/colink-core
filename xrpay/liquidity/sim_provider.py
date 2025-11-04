from dataclasses import dataclass
from decimal import Decimal, getcontext
import time

getcontext().prec = 28

@dataclass
class Pool:
    base: str
    quote: str
    x: Decimal  # base reserve
    y: Decimal  # quote reserve
    fee_bps: int = 25

class SimProvider:
    """
    Simple constant-product AMM for quotes with fee + slippage checks.
    """
    def __init__(self):
        self.pools = {
            ("XRP", "USD"): Pool("XRP", "USD", x=Decimal("1000000"), y=Decimal("600000"), fee_bps=25)
        }

    async def get_quote(self, base: str, quote: str, side: str, amount, slippageBps: int):
        amt = Decimal(str(amount))
        inv = (base, quote)
        rev = (quote, base)

        if inv in self.pools:
            pool = self.pools[inv]
            invert = False
        elif rev in self.pools:
            pool = self.pools[rev]
            invert = True
        else:
            raise ValueError("PoolNotFound")

        fee = Decimal(pool.fee_bps) / Decimal(10000)
        k = pool.x * pool.y

        if not invert:
            if side == "BUY":
                # spend quote (dy) to buy base
                dy = amt
                dy_after_fee = dy * (Decimal(1) - fee)
                x_out = pool.x - (k / (pool.y + dy_after_fee))
                exec_price = dy / x_out  # quote per base
                mid = pool.y / pool.x
                impact_bps = int(abs((exec_price - mid) / mid) * Decimal(10000))
            else:
                # sell base (dx) for quote
                dx = amt
                dx_after_fee = dx * (Decimal(1) - fee)
                y_out = pool.y - (k / (pool.x + dx_after_fee))
                exec_price = y_out / dx
                mid = pool.y / pool.x
                impact_bps = int(abs((exec_price - mid) / mid) * Decimal(10000))
        else:
            # invert pair arithmetic (treat request in the reversed orientation)
            if side == "BUY":
                # buying quoted base (which is actually pool.quote)
                dx = amt
                dx_after_fee = dx * (Decimal(1) - fee)
                y_out = pool.y - (k / (pool.x + dx_after_fee))
                exec_price = dx / y_out  # because base/quote inverted
                mid = pool.x / pool.y
                impact_bps = int(abs((exec_price - mid) / mid) * Decimal(10000))
            else:
                dy = amt
                dy_after_fee = dy * (Decimal(1) - fee)
                x_out = pool.x - (k / (pool.y + dy_after_fee))
                exec_price = x_out / dy
                mid = pool.x / pool.y
                impact_bps = int(abs((exec_price - mid) / mid) * Decimal(10000))

        if impact_bps > int(slippageBps):
            raise Exception("SlippageExceeded")

        return {
            "price": str(exec_price.quantize(Decimal("0.0000001"))),
            "fee_bps": pool.fee_bps,
            "impact_bps": impact_bps,
            "expiresAt": int(time.time()) + 15
        }

