"""
COLINK Liquidity Simulation
---------------------------
Simulates liquidity dynamics between COL, XRP, and mock COPX.
Used to test AMM stability and visualize price behavior under synthetic trades.
"""

from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Pool:
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    fee: float = 0.003

    def price(self) -> float:
        return self.reserve_b / self.reserve_a

    def swap_a_to_b(self, amount_a: float) -> float:
        amount_in_with_fee = amount_a * (1 - self.fee)
        new_reserve_a = self.reserve_a + amount_in_with_fee
        new_reserve_b = self.reserve_a * self.reserve_b / new_reserve_a
        amount_out = self.reserve_b - new_reserve_b
        self.reserve_a, self.reserve_b = new_reserve_a, new_reserve_b
        return amount_out


@dataclass
class SimulationConfig:
    steps: int = 100
    trade_size: float = 100.0
    volatility: float = 0.02
    seed: int = 42


@dataclass
class LiquiditySimulation:
    pool: Pool
    cfg: SimulationConfig
    history: dict = field(default_factory=lambda: {"price": [], "reserve_a": [], "reserve_b": []})

    def run(self):
        np.random.seed(self.cfg.seed)
        for _ in range(self.cfg.steps):
            self.history["price"].append(self.pool.price())
            self.history["reserve_a"].append(self.pool.reserve_a)
            self.history["reserve_b"].append(self.pool.reserve_b)
            direction = np.random.choice(["buy", "sell"])
            trade = self.cfg.trade_size * (1 + np.random.randn() * self.cfg.volatility)
            if direction == "buy":
                self.pool.swap_a_to_b(trade)
            else:
                self.pool.swap_a_to_b(-trade)

    def plot(self):
        plt.figure(figsize=(10, 5))
        plt.plot(self.history["price"], label="Price (B/A)")
        plt.title("Simulated COL/XRP Liquidity Pool Price Evolution")
        plt.xlabel("Step")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    pool = Pool("COL", "XRP", reserve_a=1_000_000, reserve_b=500_000)
    cfg = SimulationConfig(steps=200, trade_size=500)
    sim = LiquiditySimulation(pool, cfg)
    sim.run()
    sim.plot()
