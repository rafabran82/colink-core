import json
import pathlib
import subprocess
import sys


def test_run_demo_emits_artifacts(tmp_path: pathlib.Path):
    prefix = tmp_path / "demo"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run",
        "--demo",
        "--display",
        "Agg",
        "--out-prefix",
        str(prefix),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    png = prefix.with_suffix(".png")
    ndj = prefix.with_suffix(".ndjson")
    jsn = prefix.with_suffix(".json")

    assert png.exists() and png.stat().st_size > 0
    assert ndj.exists() and ndj.stat().st_size > 0
    assert jsn.exists() and jsn.stat().st_size > 0

    # NDJSON has multiple lines
    lines = ndj.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 10
    # JSON metrics has the required keys
    data = json.loads(jsn.read_text(encoding="utf-8"))
    for k in ["schema_version", "created_at", "backend", "sample_count", "artifacts"]:
        assert k in data
