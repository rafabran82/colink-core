from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LimitConfig:
    max_col_in: float = 25_000.0
    max_dev_bps: float = 2_000.0
    strikes_window: int = 2  # consecutive violations to trip
    cooldown_trades: int = 3  # number of blocked can_trade() calls while tripped


class TradeLimiter:
    def __init__(self, cfg: LimitConfig):
        self.cfg = cfg
        self.strikes = 0
        self.tripped = False
        self._cooldown_left = 0
        self._need_requote = False  # first check after auto-reset returns auto_reset

    def _trip(self):
        self.tripped = True
        self._cooldown_left = int(self.cfg.cooldown_trades)
        self._need_requote = False  # set after cooldown completes
        self.strikes = 0

    def can_trade(self) -> tuple[bool, str]:
        if self.tripped:
            if self._cooldown_left > 0:
                self._cooldown_left -= 1
                return False, f"circuit_breaker_tripped (cooldown_remaining={self._cooldown_left})"
            # cooldown ended -> auto-reset
            self.tripped = False
            self._need_requote = True
            return True, "auto_reset_ok"
        return True, "ok"

    def check_and_record(self, col_in: float, dev_bps: float) -> tuple[bool, str]:
        # honor auto-reset contract: first call after reset must tell caller to re-quote
        if self._need_requote:
            self._need_requote = False
            return False, "auto_reset"

        ok, reason = self.can_trade()
        if not ok and "circuit_breaker_tripped" in reason:
            return False, reason

        # size cap
        if col_in > self.cfg.max_col_in:
            self.strikes += 1
            if self.strikes >= self.cfg.strikes_window:
                self._trip()
            return False, f"size_exceeds_cap: {col_in:.6f} > {self.cfg.max_col_in:.6f}"

        # deviation cap
        if dev_bps > self.cfg.max_dev_bps:
            self.strikes += 1
            if self.strikes >= self.cfg.strikes_window:
                self._trip()
            return (
                False,
                f"twap_deviation_exceeds_cap: {dev_bps:.1f} > {self.cfg.max_dev_bps:.1f} bps",
            )

        # success clears strikes
        self.strikes = 0
        return True, "approved"
