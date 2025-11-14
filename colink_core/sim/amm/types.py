from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class PoolState:
    pair: str
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    lp_total: float
    fee_rate: float
    k: float
    timestamp: datetime


@dataclass
class SwapEvent:
    pair: str
    side: Literal["A→B", "B→A"]
    amount_in: float
    amount_out: float
    reserve_a: float
    reserve_b: float
    price: float
    slippage: float
    fee_charged: float
    timestamp: datetime


@dataclass
class LPEvent:
    pair: str
    event: Literal["mint", "burn"]
    amount_a: float
    amount_b: float
    lp_issued: float
    lp_total_after: float
    timestamp: datetime


@dataclass
class PoolSnapshot:
    pair: str
    reserve_a: float
    reserve_b: float
    price: float
    lp_total: float
    timestamp: datetime
