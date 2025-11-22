# === PR-Checks.ps1 (PowerShell-safe) ===
$ErrorActionPreference = "Stop"

Write-Host "== Byte-compile =="
Get-ChildItem -Recurse -File -Include *.py |
  Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
  ForEach-Object { python -m py_compile $_.FullName }

Write-Host "== Editable install =="
if (Test-Path .\.venv\Scripts\python.exe) {
  .\.venv\Scripts\python.exe -m pip install -e .
} else {
  Write-Warning "Venv python not found; falling back to system python"
  python -m pip install -e .
}

Write-Host "== Dev smoke =="
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Dev-Smoke.ps1

Write-Host "== Mini sweep =="
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Invoke-Sweep.ps1 -OutDir artifacts\charts -RunName pr-check

Write-Host "== Ensure summary.json (temp .py using SweepSummary) =="
$py = @"
from pathlib import Path
from colink_core.sim.summary import SweepSummary, write_summary

summary = SweepSummary(
    name="pr-check",
    ts=None,  # will be set inside writer if needed
    sizes_col=[100, 500, 1000],
    twap_guard_bps=150.0,
    avg_slip_bps=100.0,
    max_slip_bps=120.0,
    charts_dir=str(Path("artifacts/charts").resolve()),
)
out = write_summary("artifacts/summary.json", summary)
print("summary:", out)
"@

$tmp = Join-Path $env:TEMP ("write_summary_{0}.py" -f ([guid]::NewGuid()))
Set-Content -Path $tmp -Value $py -Encoding utf8
try {
  if (Test-Path .\.venv\Scripts\python.exe) {
    .\.venv\Scripts\python.exe $tmp
  } else {
    python $tmp
  }
} finally {
  Remove-Item $tmp -ErrorAction SilentlyContinue
}

Write-Host "== Metrics SLOs =="
# PowerShell 5.1-safe branch (no ternary operator)
$pyexe = "python"
if (Test-Path .\.venv\Scripts\python.exe) { $pyexe = ".\.venv\Scripts\python.exe" }

& $pyexe -m colink_core.sim.metrics `
  --dir artifacts/charts `
  --min-files 2 `
  --min-total-kb 20 `
  --summary artifacts/summary.json `
  --max-slip-bps 200

Write-Host "`nPR checks complete."

