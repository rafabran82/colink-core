from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SweepSummary:
    name: str
    ts: int
    sizes_col: list[float]
    twap_guard_bps: float
    avg_slip_bps: float
    max_slip_bps: float
    charts_dir: str


def write_summary(path: str | Path, data: SweepSummary) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(asdict(data), f, indent=2)


# Dumb demo producer for wrappers that don't compute slips:
def write_minimal(charts_dir: str, name: str = "dev", twap_guard_bps: float = 150.0) -> str:
    out = Path("artifacts/summary.json")
    # conservative defaults; engine can overwrite later with real stats
    s = SweepSummary(
        name=name,
        ts=int(time.time()),
        sizes_col=[100, 500, 1000],
        twap_guard_bps=twap_guard_bps,
        avg_slip_bps=100.0,
        max_slip_bps=120.0,
        charts_dir=str(charts_dir),
    )
    write_summary(out, s)
    return str(out)
