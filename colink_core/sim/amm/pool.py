from datetime import datetime, timezone

from .types import PoolState, SwapEvent, LPEvent, PoolSnapshot
from .swap import SwapCalculator


class AMMPool:
    """
    Hybrid AMM pool:
      - Internal math: constant-product (Uniswap v2 style)
      - Interface: XRPL-friendly (pair, LP shares, fees, snapshots)
    """

    def __init__(
        self,
        token_a: str,
        token_b: str,
        reserve_a: float,
        reserve_b: float,
        fee_rate: float = 0.003,
    ) -> None:
        self.token_a = token_a
        self.token_b = token_b
        self.pair = f"{token_a}/{token_b}"
        self.reserve_a = float(reserve_a)
        self.reserve_b = float(reserve_b)
        self.fee_rate = float(fee_rate)
        self.lp_total = 0.0
        self._init_lp()
        self.k = self.reserve_a * self.reserve_b
        self.updated_at = datetime.now(timezone.utc)
        self._swap_calc = SwapCalculator()

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _init_lp(self) -> None:
        if self.reserve_a > 0 and self.reserve_b > 0:
            self.lp_total = (self.reserve_a * self.reserve_b) ** 0.5
        else:
            self.lp_total = 0.0

    def _update_k(self) -> None:
        self.k = self.reserve_a * self.reserve_b
        self.updated_at = self._now()

    # ---------------------------
    # Public properties
    # ---------------------------

    @property
    def state(self) -> PoolState:
        return PoolState(
            pair=self.pair,
            token_a=self.token_a,
            token_b=self.token_b,
            reserve_a=self.reserve_a,
            reserve_b=self.reserve_b,
            lp_total=self.lp_total,
            fee_rate=self.fee_rate,
            k=self.k,
            timestamp=self.updated_at,
        )

    @property
    def price_a_to_b(self) -> float:
        if self.reserve_a <= 0:
            return 0.0
        return self.reserve_b / self.reserve_a

    @property
    def price_b_to_a(self) -> float:
        if self.reserve_b <= 0:
            return 0.0
        return self.reserve_a / self.reserve_b

    # ---------------------------
    # LP Minting / Burning
    # ---------------------------

    def mint_lp(self, amount_a: float, amount_b: float) -> LPEvent:
        if amount_a <= 0 or amount_b <= 0:
            raise ValueError("LP mint amounts must be positive")

        if self.lp_total == 0:
            lp_minted = (amount_a * amount_b) ** 0.5
        else:
            share_a = amount_a * self.lp_total / self.reserve_a if self.reserve_a > 0 else 0
            share_b = amount_b * self.lp_total / self.reserve_b if self.reserve_b > 0 else 0
            lp_minted = min(share_a, share_b)

        self.reserve_a += amount_a
        self.reserve_b += amount_b
        self.lp_total += lp_minted
        self._update_k()

        ts = self.updated_at
        return LPEvent(
            pair=self.pair,
            event="mint",
            amount_a=amount_a,
            amount_b=amount_b,
            lp_issued=lp_minted,
            lp_total_after=self.lp_total,
            timestamp=ts,
        )

    def burn_lp(self, lp_amount: float) -> LPEvent:
        if lp_amount <= 0:
            raise ValueError("LP burn amount must be positive")
        if lp_amount > self.lp_total:
            raise ValueError("cannot burn more LP than total supply")

        share = lp_amount / self.lp_total if self.lp_total > 0 else 0
        amount_a = self.reserve_a * share
        amount_b = self.reserve_b * share

        self.reserve_a -= amount_a
        self.reserve_b -= amount_b
        self.lp_total -= lp_amount
        self._update_k()

        ts = self.updated_at
        return LPEvent(
            pair=self.pair,
            event="burn",
            amount_a=amount_a,
            amount_b=amount_b,
            lp_issued=-lp_amount,
            lp_total_after=self.lp_total,
            timestamp=ts,
        )

    # ---------------------------
    # Swaps
    # ---------------------------

    def swap_a_to_b(self, amount_in: float) -> SwapEvent:
        if amount_in <= 0:
            raise ValueError("swap amount_in must be positive")

        result = self._swap_calc.compute_swap(
            reserve_in=self.reserve_a,
            reserve_out=self.reserve_b,
            amount_in=amount_in,
            fee_rate=self.fee_rate,
        )

        self.reserve_a += amount_in * (1.0 - self.fee_rate)
        self.reserve_b -= result.amount_out
        self._update_k()

        ts = self.updated_at
        return SwapEvent(
            pair=self.pair,
            side="A→B",
            amount_in=amount_in,
            amount_out=result.amount_out,
            reserve_a=self.reserve_a,
            reserve_b=self.reserve_b,
            price=result.price,
            slippage=result.slippage,
            fee_charged=result.fee_charged,
            timestamp=ts,
        )

    def swap_b_to_a(self, amount_in: float) -> SwapEvent:
        if amount_in <= 0:
            raise ValueError("swap amount_in must be positive")

        result = self._swap_calc.compute_swap(
            reserve_in=self.reserve_b,
            reserve_out=self.reserve_a,
            amount_in=amount_in,
            fee_rate=self.fee_rate,
        )

        self.reserve_b += amount_in * (1.0 - self.fee_rate)
        self.reserve_a -= result.amount_out
        self._update_k()

        ts = self.updated_at
        return SwapEvent(
            pair=self.pair,
            side="B→A",
            amount_in=amount_in,
            amount_out=result.amount_out,
            reserve_a=self.reserve_a,
            reserve_b=self.reserve_b,
            price=result.price,
            slippage=result.slippage,
            fee_charged=result.fee_charged,
            timestamp=ts,
        )

    # ---------------------------
    # Snapshots
    # ---------------------------

    def snapshot(self) -> PoolSnapshot:
        return PoolSnapshot(
            pair=self.pair,
            reserve_a=self.reserve_a,
            reserve_b=self.reserve_b,
            price=self.price_a_to_b,
            lp_total=self.lp_total,
            timestamp=self.updated_at,
        )
