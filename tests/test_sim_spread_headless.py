import subprocess
import sys


def test_sim_spread_headless(tmp_path):
    png = tmp_path / "spread.png"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "10",
        "--spread",
        str(png),
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert png.exists() and png.stat().st_size > 0
