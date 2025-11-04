from collections import deque
from collections.abc import Iterable


class TWAPOracle:
    """
    Simple rolling time-weighted average price (equal weights over a fixed window).
    push(price) to add a new sample; value() returns the current TWAP.
    """

    def __init__(self, window: int = 20):
        if window <= 0:
            raise ValueError("window must be > 0")
        self.window = int(window)
        self._buf = deque(maxlen=self.window)
        self._sum = 0.0

    def push(self, price: float) -> None:
        p = float(price)
        if len(self._buf) == self._buf.maxlen:
            # subtract the oldest sample that will be evicted
            self._sum -= self._buf[0]
        self._buf.append(p)
        self._sum += p

    def value(self) -> float:
        n = len(self._buf)
        return self._sum / n if n > 0 else 0.0

    def warm(self, prices: Iterable[float]) -> None:
        for p in prices:
            self.push(p)
