# --- Daily COLINK CI maintenance ---
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Definition)

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

& .\ci.rotate-artifacts.ps1 -Keep 100
& .\sim.run.ps1

python (Join-Path $PSScriptRoot "ci.aggregate-metrics.py")`nWrite-Host "✅ Daily CI maintenance complete." -ForegroundColor Green


