from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path


def build_report(
    charts_dir: str | Path = "artifacts/charts",
    summary_path: str | Path = "artifacts/summary.json",
    out_dir: str | Path = "artifacts/reports",
) -> str:
    charts_dir = Path(charts_dir)
    summary_path = Path(summary_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    charts = sorted(charts_dir.glob("*.png"))
    ts = int(time.time())
    zip_path = out_dir / f"report-{ts}.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in charts:
            if p.exists():
                z.write(p, arcname=f"charts/{p.name}")
        if summary_path.exists():
            z.write(summary_path, arcname="summary.json")
        z.writestr("README.txt", f"COLINK Phase 3 â€” charts + summary`nGenerated: {ts}`n")
    zip_path.write_bytes(buf.getvalue())
    return str(zip_path)


if __name__ == "__main__":
    print(build_report())

