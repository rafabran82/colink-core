import json
import subprocess
import sys
from pathlib import Path


def test_metrics_and_metrics_only(tmp_path: Path):
    out1 = tmp_path / "m1.json"
    png = tmp_path / "m1.png"
    # normal run (JSON + plot)
    cmd1 = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "12",
        "--pairs",
        "XRP/COL",
        "--seed",
        "101",
        "--out",
        str(out1),
        "--plot",
        str(png),
        "--display",
        "Agg",
        "--no-show",
    ]
    r1 = subprocess.run(cmd1, capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr
    assert out1.exists() and out1.stat().st_size > 0
    assert png.exists() and png.stat().st_size > 0

    d1 = json.loads(out1.read_text(encoding="utf-8"))
    assert d1["schema_version"] == "colink.sim.v1"
    assert "summary" in d1 and isinstance(d1["summary"], dict)
    s1 = d1["summary"]
    # summary smoke
    assert s1["count_points"] == 12
    assert s1["price"]["min"] > 0 and s1["price"]["max"] > 0
    assert s1["spread_bps"]["min"] <= s1["spread_bps"]["max"]

    # metrics-only: should write JSON but skip plots
    out2 = tmp_path / "m2.json"
    png2 = tmp_path / "m2.png"
    cmd2 = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "8",
        "--pairs",
        "XRP/COL",
        "--seed",
        "202",
        "--out",
        str(out2),
        "--plot",
        str(png2),
        "--metrics-only",
        "--display",
        "Agg",
        "--no-show",
    ]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr
    assert out2.exists() and out2.stat().st_size > 0
    assert not png2.exists()

