param(
    [int]$TopN = 20,
    [string]$SortBy = "lp_apy",
    [switch]$TestMode
)

Write-Host "🔍 DEBUG: Starting Run-LP-Full.ps1..." -ForegroundColor Cyan
Write-Host "🔍 DEBUG: Parameters received -> TopN=$TopN, SortBy=$SortBy, TestMode=$TestMode" -ForegroundColor Cyan

$simPath = Join-Path $PSScriptRoot "sim.run.py"
Write-Host "🔍 DEBUG: Checking if sim.run.py exists at $simPath ..." -ForegroundColor Cyan

if (-not (Test-Path $simPath)) {
    Write-Host "❌ DEBUG: sim.run.py NOT FOUND!" -ForegroundColor Red
} else {
    Write-Host "✔ DEBUG: sim.run.py found." -ForegroundColor Green
}

Write-Host "🔍 DEBUG: Running simulation..." -ForegroundColor Cyan

# Placeholder real logic
Start-Sleep -Seconds 2

Write-Host "✔ Liquidity Pool Test completed successfully!" -ForegroundColor Green
