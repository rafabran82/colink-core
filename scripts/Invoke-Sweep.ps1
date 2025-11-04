[CmdletBinding()]
param(
  [string]$OutDir = "artifacts\\charts",
  [string]$RunName = "quick-sweep"
)
$ErrorActionPreference = "Stop"
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { Write-Error "Python venv not found. Run: scripts\\Bootstrap.ps1" }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# Expecting your sweep entry to be colink_core\sim\run_sweep.py or similar
# It should write PNGs to $OutDir (or accept it via CLI env/arg).
$env:COLINK_SWEEP_OUT = $OutDir
Write-Host "==> Running sweep -> $OutDir ..."
& $python -m colink_core.sim.run_sweep --name $RunName
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Sweep complete. Files generated in $OutDir"
Get-ChildItem $OutDir -Filter *.png | ForEach-Object { Write-Host "  - " $_.FullName }
