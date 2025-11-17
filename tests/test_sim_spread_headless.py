import subprocess
import sys

import pytest

PAIRS = ["XRP/COL", "COPX/COL"]


@pytest.mark.parametrize("pair", PAIRS)
def test_sim_spread_headless(tmp_path, pair):
    png = tmp_path / "spread.png"
    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "12",
        "--spread",
        str(png),
        "--pairs",
        pair,
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert png.exists() and png.stat().st_size > 0

