import csv
import json
import subprocess
import sys
from pathlib import Path


def _write_trades_csv(p: Path):
    # t,side,size
    rows = [
        {"t": 0, "side": "buy", "size": 50},
        {"t": 1, "side": "sell", "size": 10},
        {"t": 2, "side": "buy", "size": 5},
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t", "side", "size"])
        w.writeheader()
        w.writerows(rows)


def _write_vol_csv(p: Path):
    # t,sigma
    rows = [
        {"t": 0, "sigma": 0.5},
        {"t": 1, "sigma": 1.5},
        {"t": 3, "sigma": 2.0},
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t", "sigma"])
        w.writeheader()
        w.writerows(rows)


def test_csv_ingest_headless(tmp_path: Path):
    trades = tmp_path / "trades.csv"
    vol = tmp_path / "vol.csv"
    out = tmp_path / "out.json"
    png = tmp_path / "ts.png"

    _write_trades_csv(trades)
    _write_vol_csv(vol)

    cmd = [
        sys.executable,
        "-m",
        "colink_core.sim.run_sweep",
        "--steps",
        "10",
        "--pairs",
        "XRP/COL",
        "--seed",
        "777",
        "--trades",
        str(trades),
        "--volatility",
        str(vol),
        "--out",
        str(out),
        "--plot",
        str(png),
        "--display",
        "Agg",
        "--no-show",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert out.exists() and out.stat().st_size > 0
    assert png.exists() and png.stat().st_size > 0

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "colink.sim.v1"
    assert data["seed"] == 777
    assert data["pairs"] == ["XRP/COL"]
    assert data["inputs"]["trades_csv"].endswith("trades.csv")
    assert data["inputs"]["volatility_csv"].endswith("vol.csv")
    pts = data["points"]
    assert isinstance(pts, list) and len(pts) == 10
    # sanity on first point presence
    p0 = pts[0]
    assert p0["t"] == 0 and p0["spread_bps"] == 10.0

