import pathlib
import subprocess
import sys


def test_sim_demo_plot(tmp_path: pathlib.Path):
    out = tmp_path / "demo.png"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--demo",
        "--display",
        "Agg",
        "--out",
        str(out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert out.exists() and out.stat().st_size > 0

