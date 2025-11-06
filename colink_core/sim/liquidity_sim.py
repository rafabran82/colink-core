from __future__ import annotations


class LiquiditySim:
    """Simple constant-product AMM (x*y=k) with a fee on input."""

    def __init__(self, reserve_a: float, reserve_b: float, fee: float = 0.003) -> None:
        self.reserve_a = float(reserve_a)
        self.reserve_b = float(reserve_b)
        self.fee = float(fee)

    def price_a_in_b(self) -> float:
        # price of 1 A in units of B (B/A)
        return self.reserve_b / self.reserve_a

    def swap_a_to_b(self, amount_a: float) -> float:
        """Trade A for B; returns B out."""
        amount_in_with_fee = float(amount_a) * (1.0 - self.fee)
        new_reserve_a = self.reserve_a + amount_in_with_fee
        # keep invariant approximately constant (x*y=k)
        new_reserve_b = (self.reserve_a * self.reserve_b) / new_reserve_a
        out_b = self.reserve_b - new_reserve_b
        self.reserve_a = new_reserve_a
        self.reserve_b = new_reserve_b
        return out_b

    def swap_b_to_a(self, amount_b: float) -> float:
        """Trade B for A; returns A out."""
        amount_in_with_fee = float(amount_b) * (1.0 - self.fee)
        new_reserve_b = self.reserve_b + amount_in_with_fee
        new_reserve_a = (self.reserve_a * self.reserve_b) / new_reserve_b
        out_a = self.reserve_a - new_reserve_a
        self.reserve_b = new_reserve_b
        self.reserve_a = new_reserve_a
        return out_a
