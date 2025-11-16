. "$PSScriptRoot\scripts\Show-LP-Dashboard.ps1"

param(
    [int]$TopN = 20,
    [switch]$TestMode
)

Write-Host "▶ Running LP Simulation..." -ForegroundColor Cyan

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
$metricsPath = Join-Path $PSScriptRoot "scripts\.artifacts\data\lp_metrics.json"

if (-not (Test-Path $metricsPath)) {
    Write-Host "❌ Metrics file not found: $metricsPath" -ForegroundColor Red
    exit 1
}

$data = Get-Content $metricsPath | ConvertFrom-Json

if ($null -eq $data -or $data.Count -eq 0) {
    Write-Host "❌ No LP data available" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------
# Select Top LPs
# ------------------------------------------------------------
$top = $data | Sort-Object -Property lp_apy -Descending | Select-Object -First $TopN

# ------------------------------------------------------------
# Compute Metrics
# ------------------------------------------------------------
$avgDrawdown  = ($top | Measure-Object -Property lp_drawdown_abs_mean -Average).Average
$avgVol       = ($top | Measure-Object -Property lp_volatility_abs_mean -Average).Average
$totalShocks  = ($top | Measure-Object -Property total_shocks -Sum).Sum
$avgAPY       = ($top | Measure-Object -Property lp_apy -Average).Average

$maxDrawdown  = ($top | Measure-Object -Property lp_drawdown_abs_mean -Maximum).Maximum
$maxVolatility = ($top | Measure-Object -Property lp_volatility_abs_mean -Maximum).Maximum
$maxShocks    = ($top | Measure-Object -Property total_shocks -Maximum).Maximum

# ------------------------------------------------------------
# Health Check Summary
# ------------------------------------------------------------
$issues = @()

if ($avgDrawdown -gt 0.05) { $issues += "Drawdown high" }
if ($avgVol -gt 0.04)      { $issues += "Volatility high" }
if ($totalShocks -gt 0)    { $issues += "Shocks detected" }
if ($avgAPY -lt 8)         { $issues += "APY low" }

if ($issues.Count -gt 0) {
    Write-Host "⚠️ Health Issues: $($issues -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "🟢 LP System Healthy" -ForegroundColor Green
}

# ------------------------------------------------------------
# Logging Summary
# ------------------------------------------------------------
$summaryFolder = Join-Path $PSScriptRoot "scripts\.artifacts\data"
if (-not (Test-Path $summaryFolder)) { New-Item -ItemType Directory -Path $summaryFolder | Out-Null }

$timestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")

$summary = [ordered]@{
    timestamp     = $timestamp
    avgDrawdown   = $avgDrawdown
    avgVolatility = $avgVol
    totalShocks   = $totalShocks
    avgAPY        = $avgAPY
    topN          = $TopN
}

$summaryPath = Join-Path $summaryFolder "lp_summary_$timestamp.json"
$summary | ConvertTo-Json -Depth 5 | Set-Content -Path $summaryPath -Encoding UTF8
Write-Host "💾 Saved LP summary → $summaryPath" -ForegroundColor Cyan

# ------------------------------------------------------------
# Reward Distribution
# ------------------------------------------------------------
$RewardPool = 1000
Write-Host "💰 Reward pool: $RewardPool COL" -ForegroundColor Cyan

$rewards = Distribute-LP-Rewards -TopLPs $top -TestMode:$TestMode -RewardPool $RewardPool

$rewardOut = Join-Path $summaryFolder "lp_rewards_output_$timestamp.json"
$rewards | ConvertTo-Json -Depth 5 | Set-Content -Path $rewardOut -Encoding UTF8
Write-Host "💾 Rewards saved → $rewardOut" -ForegroundColor Green

Write-Host "✔ Run complete" -ForegroundColor Green
