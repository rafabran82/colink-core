import json
import subprocess
import sys
from pathlib import Path


def test_sim_json_schema_and_seed(tmp_path: Path):
    jsn = tmp_path / "m.json"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "5",
        "--out",
        str(jsn),
        "--pairs",
        "XRP/COL",
        "--seed",
        "123",
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert jsn.exists() and jsn.stat().st_size > 0

    data = json.loads(jsn.read_text(encoding="utf-8"))
    # header presence
    assert data["schema_version"] == "colink.sim.v1"
    assert data["seed"] == 123
    assert data["pairs"] == ["XRP/COL"]
    assert isinstance(data["generated_at"], str) and data["generated_at"].endswith("Z")

    pts = data["points"]
    assert isinstance(pts, list) and len(pts) == 5
    # determinism smoke: ensure first two points are stable for seed=123
    p0, p1 = pts[0], pts[1]
    # exact time indices
    assert p0["t"] == 0 and p1["t"] == 1

    # tolerate tiny float drift across Python minor versions
    def approx(a, b, tol=1e-9):
        return abs(a - b) <= tol

    assert approx(p0["price"], 1.0028770486800365)
    assert approx(p0["spread_bps"], 10.0)
    assert p0["depth"] > 0
    assert p1["price"] > 0 and p1["depth"] > 0
