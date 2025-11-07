import json
import subprocess
import sys
from pathlib import Path

PKG = ["-m", "colink_core.sim.json_cli"]


def run(args):
    p = subprocess.run([sys.executable, *PKG, *args], capture_output=True, text=True)
    assert p.returncode == 0, f"returncode={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}"
    return p.stdout.strip()


def test_help_is_ascii_and_clean():
    out = run(["--help"])
    out.encode("ascii", "strict")  # raises if non-ASCII
    assert "quote calculation -> JSON" in out
    assert "generate sweep charts -> JSON list of files" in out


def test_quote_basic():
    out = run(["quote", "--col-in", "100", "--min-out-bps", "5"])
    obj = json.loads(out)
    assert obj["col_in"] == 100.0
    assert obj["min_out_bps"] == 5.0
    assert obj["eff_copx_per_col"] > 0.99


def test_sweep_placeholder(tmp_path: Path):
    outdir = tmp_path / "charts"
    out = run(["sweep", "--outdir", str(outdir), "--n-paths", "3", "--n-steps", "8"])
    obj = json.loads(out)
    charts = obj.get("charts")
    assert isinstance(charts, list) and len(charts) == 2
    # Only assert path prefix; files may be PNGs or small text files depending on env
    for p in charts:
        assert str(p).startswith(str(outdir))
