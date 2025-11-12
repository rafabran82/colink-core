# --- Daily COLINK CI maintenance (robust paths) ---
# Resolve scriptDir for both script execution and interactive runs
if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} else {
  $repo = (& git rev-parse --show-toplevel 2>$null)
  if ($repo) { $scriptDir = Join-Path $repo "scripts" } else { $scriptDir = Join-Path (Get-Location).Path "scripts" }
}

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

# Rotate artifacts
& (Join-Path $scriptDir "ci.rotate-artifacts.ps1") -Keep 100

# Sim run
& (Join-Path $scriptDir "sim.run.ps1")

# Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# Embed latest metrics panel into index.html
& (Join-Path $scriptDir "ci.embed-latest.ps1")

Write-Host "✅ Daily CI maintenance complete." -ForegroundColor Green
