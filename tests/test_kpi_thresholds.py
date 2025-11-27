import json
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / ".artifacts"

MIN_SR = float(os.environ.get("COLINK_MIN_SUCCESS_RATE", "0.95"))
MAX_P95 = float(os.environ.get("COLINK_MAX_P95_MS", "250.0"))


def metrics_jsons():
    return sorted(ART.rglob("*.metrics.json"))


@pytest.mark.parametrize("path", metrics_jsons())
def test_kpi_thresholds(path: pathlib.Path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    m = data.get("metrics", {})
    sr = m.get("success_rate")
    p95 = m.get("p95_latency_ms")

    # Skip when demo/wrapped outputs don't provide numeric KPIs
    if sr is None and p95 is None:
        pytest.skip("No KPIs present yet (demo/wrapped).")

    if sr is not None:
        assert float(sr) >= MIN_SR, f"success_rate too low: {sr} < {MIN_SR}"

    if p95 is not None:
        assert float(p95) <= MAX_P95, f"p95_latency_ms too high: {p95} > {MAX_P95}"

