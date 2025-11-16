param(
    [int]$TopN = 20,
    [switch]$TestMode
)
# --- Load dashboard module ---
. "$PSScriptRoot\scripts\Show-LP-Dashboard.ps1"
. "$PSScriptRoot\scripts\Distribute-LP-Rewards.ps1"

Write-Host "=== LAYER 1 OK ===" -ForegroundColor Green
Write-Host "TopN: $TopN" -ForegroundColor Cyan
Write-Host "TestMode: $TestMode" -ForegroundColor Cyan



# ============================================================
# LAYER 3 ? Load Metrics + Compute
# ============================================================

Write-Host "=== LAYER 3 ===" -ForegroundColor Yellow

$metricsPath = Join-Path $PSScriptRoot "scripts\.artifacts\data\lp_metrics.json"

if (-not (Test-Path $metricsPath)) {
    Write-Host "? Metrics file missing: $metricsPath" -ForegroundColor Red
}

$data = Get-Content $metricsPath | ConvertFrom-Json

if ($null -eq $data -or $data.Count -eq 0) {
    Write-Host "? No LP data found" -ForegroundColor Red
}

$top = $data | Sort-Object -Property lp_apy -Descending | Select-Object -First $TopN

$avgDrawdown  = ($top | Measure-Object lp_drawdown_abs_mean -Average).Average
$avgVol       = ($top | Measure-Object lp_volatility_abs_mean -Average).Average
$totalShocks  = ($top | Measure-Object total_shocks -Sum).Sum
$avgAPY       = ($top | Measure-Object lp_apy -Average).Average

Write-Host "Metrics loaded." -ForegroundColor Green


# ============================================================
# LAYER 4 ? Health Summary
# ============================================================

Write-Host "=== LAYER 4 ===" -ForegroundColor Yellow

$issues = @()

if ($avgDrawdown -gt 0.04) { $issues += "Drawdown high" }
if ($avgVol -gt 0.03)      { $issues += "Volatility high" }
if ($totalShocks -gt 0)    { $issues += "Shocks detected" }
if ($avgAPY -lt 8)         { $issues += "APY low" }

if ($issues.Count -eq 0) {
    Write-Host "?? System Healthy" -ForegroundColor Green
} else {
    Write-Host "?? Health Issues:" -ForegroundColor Yellow
    $issues | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
}

# ============================================================
# LAYER 5 ? Logging & Summary File Output
# ============================================================

Write-Host "=== LAYER 5 ===" -ForegroundColor Yellow

$summaryFolder = Join-Path $PSScriptRoot "scripts\.artifacts\data"
if (-not (Test-Path $summaryFolder)) {
    New-Item -ItemType Directory -Path $summaryFolder -Force | Out-Null
}

$timestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")

$summary = [ordered]@{
    timestamp     = $timestamp
    TopN          = $TopN
    avgDrawdown   = $avgDrawdown
    avgVolatility = $avgVol
    totalShocks   = $totalShocks
    avgAPY        = $avgAPY
}

$summaryPath = Join-Path $summaryFolder "lp_summary_$timestamp.json"
$summary | ConvertTo-Json -Depth 5 | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "?? Summary saved ? $summaryPath" -ForegroundColor Cyan

# ============================================================
# LAYER 6 ? Reward Distribution
# ============================================================

Write-Host "=== LAYER 6 ===" -ForegroundColor Yellow

$RewardPool = 1000  # fixed for now

if (-not (Get-Command "Distribute-LP-Rewards" -ErrorAction SilentlyContinue)) {
    Write-Host "? Reward function not found: Distribute-LP-Rewards" -ForegroundColor Red
    Write-Host "Skipping rewards..." -ForegroundColor Yellow
    return
}

$rewards = Distribute-LP-Rewards -TopLPs $top -RewardPool $RewardPool -TestMode:$TestMode

$rewardOut = Join-Path $summaryFolder "lp_rewards_$timestamp.json"
$rewards | ConvertTo-Json -Depth 5 | Set-Content -Path $rewardOut -Encoding UTF8

Write-Host "?? Rewards saved ? $rewardOut" -ForegroundColor Green


