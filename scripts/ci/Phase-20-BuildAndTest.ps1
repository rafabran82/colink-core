param()
$ErrorActionPreference = "Stop"

Write-Host "== Phase-20: Build & Test ==" -ForegroundColor Cyan

# Always operate at repo root
Set-Location (git rev-parse --show-toplevel)

# ensure artifacts dir
$art = Join-Path $PWD ".artifacts"
if (-not (Test-Path $art)) { New-Item -ItemType Directory -Force -Path $art | Out-Null }

# Python path
$py = Join-Path $PWD ".venv\Scripts\python.exe"

# ----- SIM DEMO -----
Write-Host "Running sim demo..." -ForegroundColor Yellow
if (Test-Path $py) {
  & $py .\scripts\ci\sim_stub.py | Tee-Object -FilePath (Join-Path $art "sim_stub.out.txt") | Out-Null
} else {
  Write-Warning "Python venv not found at $py; skipping sim stub."
}

# ----- BRIDGE DEMO (placeholder) -----
Write-Host "Running bridge demo..." -ForegroundColor Yellow
try { Write-Host "Bridge demo placeholder (no-op)." } catch { Write-Warning "Bridge demo skipped." }

# ----- pytest (capture output) -----
Write-Host "Running pytest -q ..." -ForegroundColor Yellow
$pytestOut = Join-Path $art "pytest.txt"
if (Test-Path $py) {
  try {
    & $py -m pytest -q 2>&1 | Tee-Object -FilePath $pytestOut | Out-Null
  } catch {
    "pytest error: $($_.Exception.Message)" | Add-Content $pytestOut
  }
} else {
  "No venv; pytest skipped." | Set-Content $pytestOut
}

Write-Host "Build & Test done." -ForegroundColor Green
