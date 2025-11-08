import json, sys, subprocess, pathlib

def test_bridge_smoke(tmp_path: pathlib.Path):
    out_prefix = tmp_path / "bridge_demo"
    cmd = [
        sys.executable, "-m", "colink_core.bridge.run",
        "--amount", "1500",
        "--pairA", "COL/COPX",
        "--pairM", "COPX/XRP",
        "--out-prefix", str(out_prefix),
        "--backend", "Agg",
        "--sha", "deadbeef"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    m = json.loads(out_prefix.with_suffix(".metrics.json").read_text(encoding="utf-8"))
    assert m["schema_version"] == "colink.bridge.v1"
    assert m["metrics"]["slippage_bps"] >= 0
    assert m["metrics"]["amount_out"] > 0
