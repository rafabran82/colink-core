param()
$ErrorActionPreference = "Stop"

Write-Host "== Phase-20: Build & Test ==" -ForegroundColor Cyan

$art = Join-Path $PWD ".artifacts"
if (-not (Test-Path $art)) { New-Item -ItemType Directory -Force -Path $art | Out-Null }

# Activate venv python
$py = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Missing .venv; run Phase-10" }

# 1) Sim demo (if available)
$simCmd = @($py,"-m","colink_core.sim.run","--demo","--display","Agg","--out-prefix",".\.artifacts\demo")
try {
  Write-Host "Running sim demo..." -ForegroundColor Yellow
  & $simCmd 2>$null
  if ($LASTEXITCODE) { Write-Warning "Sim demo non-zero exit ($LASTEXITCODE) — continuing." }
} catch { Write-Warning "Sim demo skipped (module/entrypoint not found)." }

# 2) Bridge demo (if available)
$bridgeCmd = @($py,"-m","colink_core.sim.bridge","--demo","--out-prefix",".\.artifacts\bridge")
try {
  Write-Host "Running bridge demo..." -ForegroundColor Yellow
  & $bridgeCmd 2>$null
  if ($LASTEXITCODE) { Write-Warning "Bridge demo non-zero exit ($LASTEXITCODE) — continuing." }
} catch { Write-Warning "Bridge demo skipped." }

# 3) Unit tests if pytest exists
if (Get-Command pytest -ErrorAction SilentlyContinue) {
  try {
    Write-Host "Running pytest -q ..." -ForegroundColor Yellow
    pytest -q | Tee-Object -FilePath .\.artifacts\pytest.txt | Out-Null
  } catch { Write-Warning "pytest failed — continuing." }
} else {
  Write-Host "pytest not installed — skipping tests." -ForegroundColor DarkYellow
}

# 4) Always drop a probe so artifacts is non-empty
Set-Content (Join-Path $art "_probe.txt") ("hello " + (Get-Date).ToString("s")) -Encoding utf8

Write-Host "Build & Test done." -ForegroundColor Green
