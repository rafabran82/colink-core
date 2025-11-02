import json
import subprocess
import sys

def _run_json(args):
    out = subprocess.check_output([sys.executable, "-m"] + args, stderr=subprocess.STDOUT)
    return json.loads(out.decode("utf-8"))

def test_quote_json_smoke():
    data = _run_json(["colink_core.sim.json_cli", "quote", "--col-in", "8000", "--min-out-bps", "150", "--twap-guard"])
    assert set(["col_in","copx_out","eff_copx_per_col","min_out_bps","min_out","twap_guard","raw"]).issubset(data.keys())
    assert isinstance(data["col_in"], (int,float))
    assert isinstance(data["copx_out"], (int,float))
    assert data["eff_copx_per_col"] > 0

def test_sweep_json_smoke(tmp_path):
    outdir = tmp_path.as_posix()
    data = _run_json(["colink_core.sim.json_cli", "sweep", "--outdir", outdir])
    # Should produce at least one chart; CSV optional
    assert isinstance(data["charts"], list)
    assert len(data["charts"]) >= 1