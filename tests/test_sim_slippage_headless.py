import subprocess
import sys


def test_sim_slippage_headless(tmp_path):
    png = tmp_path / "slip.png"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "5",
        "--slippage",
        str(png),
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert png.exists() and png.stat().st_size > 0
