import subprocess
import sys


def test_sim_headless_agg(tmp_path):
    png = tmp_path / "sim.png"
    jsn = tmp_path / "sim.json"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "10",
        "--plot",
        str(png),
        "--out",
        str(jsn),
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert png.exists() and png.stat().st_size > 0
    assert jsn.exists() and jsn.stat().st_size > 0
