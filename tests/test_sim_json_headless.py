import json
import subprocess
import sys
from pathlib import Path


def _run(seed: int, tmp_path: Path):
    jsn = tmp_path / f"m_{seed}.json"
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
        str(seed),
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    data = json.loads(jsn.read_text(encoding="utf-8"))
    return data


def test_sim_json_schema_and_seed(tmp_path: Path):
    # --- schema + header checks (seed 123) ---
    data = _run(123, tmp_path)
    assert data["schema_version"] == "colink.sim.v1"
    assert data["seed"] == 123
    assert data["pairs"] == ["XRP/COL"]
    assert isinstance(data["generated_at"], str) and data["generated_at"].endswith("Z")

    pts = data["points"]
    assert isinstance(pts, list) and len(pts) == 5
    p0, p1 = pts[0], pts[1]
    assert p0["t"] == 0 and p1["t"] == 1
    # spread at t=0 comes from sin(0) = 0 → 10.0 bps, seed-independent
    assert p0["spread_bps"] == 10.0

    # --- determinism by comparison ---
    data_same = _run(123, tmp_path)
    pts_same = data_same["points"]

    # Same seed → identical first point within tiny tolerance
    def approx(a, b, tol=1e-12):  # tight, but not bit-exact
        return abs(a - b) <= tol

    assert approx(pts_same[0]["price"], p0["price"])
    assert approx(pts_same[0]["depth"], p0["depth"])

    # Different seed → first point differs (very likely on price or depth)
    data_other = _run(456, tmp_path)
    pts_other = data_other["points"]
    assert not approx(pts_other[0]["price"], p0["price"]) or not approx(
        pts_other[0]["depth"], p0["depth"]
    )
