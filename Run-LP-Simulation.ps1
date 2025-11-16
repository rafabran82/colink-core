. "$PSScriptRoot\scripts\Show-LP-Dashboard.ps1"

param(
    [int]$TopN = 20,
    [switch]$TestMode
)

Write-Host "▶ Running LP Simulation..." -ForegroundColor Cyan
Write-Host "▶ Running LP Simulation..." -ForegroundColor Cyan

# Load pools.json or metrics file
$metricsPath = Join-Path $PSScriptRoot "scripts\.artifacts\data\lp_metrics.json"
if (-not (Test-Path $metricsPath)) {
    
