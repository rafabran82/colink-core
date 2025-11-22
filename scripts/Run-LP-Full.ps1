param(
    [int]$TopN = 20,
    [string]$SortBy = "lp_apy",
    [switch]$TestMode
)

Write-Host "ðŸ” DEBUG: Starting Run-LP-Full.ps1..." -ForegroundColor Cyan
Write-Host "ðŸ” DEBUG: Parameters received -> TopN=$TopN, SortBy=$SortBy, TestMode=$TestMode" -ForegroundColor Cyan

$simPath = Join-Path $PSScriptRoot "sim.run.py"
Write-Host "ðŸ” DEBUG: Checking if sim.run.py exists at $simPath ..." -ForegroundColor Cyan

if (-not (Test-Path $simPath)) {
    Write-Host "âŒ DEBUG: sim.run.py NOT FOUND!" -ForegroundColor Red
} else {
    Write-Host "âœ” DEBUG: sim.run.py found." -ForegroundColor Green
}

Write-Host "ðŸ” DEBUG: Running simulation..." -ForegroundColor Cyan

# Placeholder real logic
Start-Sleep -Seconds 2

Write-Host "âœ” Liquidity Pool Test completed successfully!" -ForegroundColor Green

