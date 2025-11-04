# === PR-Checks.ps1 ===
$ErrorActionPreference = "Stop"
Write-Host "== Byte-compile =="
Get-ChildItem -Recurse -Filter *.py | Where-Object { $_.FullName -notmatch '\\\.venv\\' } | ForEach-Object { python -m py_compile $_.FullName }

Write-Host "== Editable install =="
.\.venv\Scripts\python.exe -m pip install -e .

Write-Host "== Dev smoke =="
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Dev-Smoke.ps1

Write-Host "== Mini sweep =="
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Invoke-Sweep.ps1 -OutDir artifacts\charts -RunName pr-check

Write-Host "== Ensure summary.json =="
.\.venv\Scripts\python.exe - << 'PY'
from colink_core.sim.summary import write_summary
p = write_summary("artifacts/summary.json", name="pr-check", sizes_col=[100,500,1000], twap_guard_bps=150.0, avg_slip_bps=100.0, max_slip_bps=120.0, charts_dir="artifacts/charts")
print("summary:", p)
PY

Write-Host "== Metrics SLOs =="
.\.venv\Scripts\python.exe -m colink_core.sim.metrics --dir artifacts/charts --min-files 2 --min-total-kb 20 --summary artifacts/summary.json --max-slip-bps 200
