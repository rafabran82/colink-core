def test_sweep_returns_pngs(tmp_path):
    import json
    import os
    import subprocess
    import sys

    outdir = tmp_path.as_posix()
    out = subprocess.check_output(
        [sys.executable, "-m", "colink_core.sim.json_cli", "sweep", "--outdir", outdir]
    )
    data = json.loads(out.decode("utf-8"))
    assert isinstance(data["charts"], list) and len(data["charts"]) >= 1
    for p in data["charts"]:
        assert p.endswith(".png")
        assert (tmp_path / os.path.basename(p)).exists()
