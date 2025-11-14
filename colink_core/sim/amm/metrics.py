from __future__ import annotations

from typing import Dict
from .types import PoolState, SwapEvent


class MetricsEngine:
    """
    Computes derived metrics for AMM pool events.
    This is intentionally minimal for Step A, expanded later in Step B.
    """

    def compute_from_state(self, state: PoolState) -> Dict[str, float]:
        """
        Compute metrics based solely on pool state.
        """
        if state.reserve_a > 0:
            price = state.reserve_b / state.reserve_a
        else:
            price = 0.0

        depth = min(state.reserve_a, state.reserve_b)

        return {
            "price": price,
            "depth": depth,
        }

    def compute_from_swap(self, event: SwapEvent) -> Dict[str, float]:
        """
        Compute metrics based on a swap event.
        """
        return {
            "price": event.price,
            "slippage": event.slippage,
            "fee": event.fee_charged,
        }
