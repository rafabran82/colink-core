import json, pathlib, pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART  = ROOT / ".artifacts"

def metrics_jsons():
    return sorted(p for p in ART.rglob("*.metrics.json"))

@pytest.mark.parametrize("path", metrics_jsons())
def test_kpi_thresholds(path: pathlib.Path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    m = data.get("metrics", {})
    sr  = m.get("success_rate")
    p95 = m.get("p95_latency_ms")

    if sr is None and p95 is None:
        pytest.skip("No KPIs present yet (wrapped demo).")

    if sr is not None:
        assert sr >= 0.95, f"success_rate too low: {sr}"

    if p95 is not None:
        assert p95 <= 250, f"p95_latency_ms too high: {p95}"
