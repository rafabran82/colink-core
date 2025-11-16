param(
    [int]$TopN = 20,
    [switch]$TestMode
)
# --- Load dashboard module ---
. "$PSScriptRoot\scripts\Show-LP-Dashboard.ps1"

Write-Host "=== LAYER 1 OK ===" -ForegroundColor Green
Write-Host "TopN: $TopN" -ForegroundColor Cyan
Write-Host "TestMode: $TestMode" -ForegroundColor Cyan

return 0


# ============================================================
# LAYER 3 ? Load Metrics + Compute
# ============================================================

Write-Host "=== LAYER 3 ===" -ForegroundColor Yellow

$metricsPath = Join-Path $PSScriptRoot "scripts\.artifacts\data\lp_metrics.json"

if (-not (Test-Path $metricsPath)) {
    Write-Host "? Metrics file missing: $metricsPath" -ForegroundColor Red
    return
}

$data = Get-Content $metricsPath | ConvertFrom-Json

if ($null -eq $data -or $data.Count -eq 0) {
    Write-Host "? No LP data found" -ForegroundColor Red
    return
}

$top = $data | Sort-Object -Property lp_apy -Descending | Select-Object -First $TopN

$avgDrawdown  = ($top | Measure-Object lp_drawdown_abs_mean -Average).Average
$avgVol       = ($top | Measure-Object lp_volatility_abs_mean -Average).Average
$totalShocks  = ($top | Measure-Object total_shocks -Sum).Sum
$avgAPY       = ($top | Measure-Object lp_apy -Average).Average

Write-Host "Metrics loaded." -ForegroundColor Green
