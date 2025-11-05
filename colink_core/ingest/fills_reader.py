from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Fill:
    ts: dt.datetime  # UTC naive
    side: str  # "buy"/"sell"
    col_in: float
    copx_out: float
    price: float  # COPX/COL at execution
    slip_bps: float  # (twap - exec)/twap * 10_000
    notes: str = ""


def parse_ts(x: str) -> dt.datetime:
    # Accept ISO8601 or unix seconds
    x = x.strip()
    if x.isdigit():
        return dt.datetime.utcfromtimestamp(int(x))
    try:
        # 2025-11-04T13:20:00Z / 2025-11-04 13:20:00
        x = x.replace("Z", "")
        return dt.datetime.fromisoformat(x)
    except Exception as err:
        raise ValueError(f"Unrecognized timestamp: {x}") from err


def read_fills_csv(path: Path | str) -> list[Fill]:
    path = Path(path)
    fills: list[Fill] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"ts", "side", "col_in", "copx_out", "price", "slip_bps"}
        missing = required - set(map(str.lower, r.fieldnames or []))
        if missing:
            # Try case-sensitive keys before failing
            missing2 = required - set(r.fieldnames or [])
            if missing2:
                raise ValueError(f"CSV missing required columns: {sorted(missing2)}")

        for row in r:

            def pick(k: str, _row=row) -> str:
                return _row.get(k, _row.get(k.lower(), ""))

            ts = parse_ts(pick("ts"))
            side = (pick("side") or "").lower()
            if side not in {"buy", "sell"}:
                raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")

            col_in = float(pick("col_in"))
            copx_out = float(pick("copx_out"))
            price = float(pick("price"))
            slip_bps = float(pick("slip_bps"))
            notes = pick("notes") or ""
            fills.append(Fill(ts, side, col_in, copx_out, price, slip_bps, notes))
    return fills
