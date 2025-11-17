from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_api_quote_ok():
    r = client.get("/sim/quote", params={"col_in": 8000, "min_out_bps": 150, "twap_guard": True})
    assert r.status_code == 200
    j = r.json()
    assert j["col_in"] == 8000.0
    assert j["min_out_bps"] == 150.0
    assert j["min_out"] == pytest.approx(7880.0)
    assert j["eff_copx_per_col"] == pytest.approx(0.985)


def test_api_sweep_ok(tmp_path: Path):
    r = client.post("/sim/sweep", params={"outdir": str(tmp_path)})
    assert r.status_code == 200
    j = r.json()
    assert "charts" in j and len(j["charts"]) == 2
    # ensure files exist in the requested outdir
    for p in j["charts"]:
        assert (tmp_path / Path(p).name).exists()

