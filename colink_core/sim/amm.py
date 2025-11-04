from __future__ import annotations

import math


class PoolState:
    def __init__(self, x_reserve: float, y_reserve: float, fee_bps: float = 30):
        self.x_reserve = float(x_reserve)
        self.y_reserve = float(y_reserve)
        self.fee_bps   = float(fee_bps)

        # LP supply (initialize from current reserves so seed() has non-zero LP)
        k = max(self.x_reserve * self.y_reserve, 0.0)
        self.total_lp = math.sqrt(k) if k > 0 else 0.0

        # Optional fee tallies for demos; harmless for tests
        self.lp_fee_x = 0.0
        self.lp_fee_y = 0.0
        self.protocol_fee_x = 0.0
        self.protocol_fee_y = 0.0

    # ----- Swaps (unchanged math; constant-product with fee) -----
    def _apply_fee(self, amount: float) -> float:
        return amount * (1.0 - self.fee_bps / 1e4)

    def swap_x_for_y(self, dx: float) -> tuple[float, float]:
        dx_eff = self._apply_fee(dx)
        x_new = self.x_reserve + dx_eff
        k = self.x_reserve * self.y_reserve
        y_new = k / x_new
        dy_out = self.y_reserve - y_new
        self.x_reserve += dx
        self.y_reserve -= dy_out
        eff_price = dy_out / dx if dx > 0 else 0.0
        return dy_out, eff_price

    def swap_y_for_x(self, dy: float) -> tuple[float, float]:
        dy_eff = self._apply_fee(dy)
        y_new = self.y_reserve + dy_eff
        k = self.x_reserve * self.y_reserve
        x_new = k / y_new
        dx_out = self.x_reserve - x_new
        self.y_reserve += dy
        self.x_reserve -= dx_out
        eff_price = dx_out / dy if dy > 0 else 0.0
        return dx_out, eff_price

    # ----- Liquidity -----
    def add_liquidity(self, dx: float, dy: float) -> float:
        """
        Proportional mint:
          - if first LP: mint sqrt(dx*dy)
          - else: mint min(dx/x, dy/y) * total_lp
        Reserves add the provided dx, dy.
        Returns minted LP.
        """
        dx = float(dx)
        dy = float(dy)
        if dx <= 0 or dy <= 0:
            return 0.0

        if self.total_lp <= 0:
            minted = math.sqrt(dx * dy)
            self.x_reserve += dx
            self.y_reserve += dy
            self.total_lp = minted
            return minted

        # Existing pool: mint proportionally
        rx = self.x_reserve
        ry = self.y_reserve
        m = min(dx / rx, dy / ry)
        minted = m * self.total_lp
        self.x_reserve += dx
        self.y_reserve += dy
        self.total_lp += minted
        return minted

    def remove_liquidity(self, fraction: float) -> tuple[float, float]:
        """
        Burn a fraction of total LP and return proportional reserves.
        Example: fraction=0.10 withdraws 10% of each reserve.
        """
        fraction = float(fraction)
        if fraction <= 0:
            return 0.0, 0.0
        fraction = min(fraction, 1.0)

        dx = self.x_reserve * fraction
        dy = self.y_reserve * fraction
        self.x_reserve -= dx
        self.y_reserve -= dy
        self.total_lp *= (1.0 - fraction)
        return dx, dy


