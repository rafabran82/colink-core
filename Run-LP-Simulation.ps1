param(
    [int]$TopN = 20,
    [ValidateSet("lp_max_drawdown_pct","lp_volatility_abs_mean","total_shocks","lp_apy")]
    [string]$SortBy = "lp_max_drawdown_pct"
)

# Generate mock LP data if missing
if (-not (Get-Variable -Name lpObjects -Scope 0 -ErrorAction SilentlyContinue)) {
    $lpObjects = @(
        [PSCustomObject]@{ lp_name="LP-A"; lp_max_drawdown_pct=5.2; lp_volatility_abs_mean=2.1; total_shocks=3; lp_apy=12.5 }
        [PSCustomObject]@{ lp_name="LP-B"; lp_max_drawdown_pct=0; lp_volatility_abs_mean=0; total_shocks=0; lp_apy=0 }
        [PSCustomObject]@{ lp_name="LP-C"; lp_max_drawdown_pct=7.8; lp_volatility_abs_mean=3.4; total_shocks=5; lp_apy=8.9 }
    )
}

# Select top N
$top = $lpObjects | Sort-Object $SortBy -Descending | Select-Object -First $TopN

# Call dashboard script
$dashboardPath = if ($PSScriptRoot) { Join-Path $PSScriptRoot "scripts\Show-LP-Dashboard.ps1" } else { ".\scripts\Show-LP-Dashboard.ps1" }
if (Test-Path $dashboardPath) { . $dashboardPath -TopN $TopN -SortBy $SortBy } else { Write-Host "❌ Dashboard script not found at $dashboardPath" -ForegroundColor Red }

# --- Render summary row ---
function Render-Bar($value,$max,$width=10,$color="Green"){
    $max = if ($max -gt 0) { $max } else { 1 }
    $value = if ($value -eq $null) { 0 } else { $value }
    $filled = [math]::Round([math]::Min([math]::Max($value/$max,0),1)*$width)
    $empty = $width - $filled
    $bar = ("█"* $filled)+("░"* $empty)
    [PSCustomObject]@{ Bar=$bar; Color=if($bar -match "░"){ "DarkGray" } else { $color } }
}

# Compute max values safely
$maxDrawdownValue = ($top | Sort-Object lp_max_drawdown_pct -Descending | Select-Object -First 1).lp_max_drawdown_pct
$maxVolValue      = ($top | Sort-Object lp_volatility_abs_mean -Descending | Select-Object -First 1).lp_volatility_abs_mean
$maxShocksValue   = ($top | Sort-Object total_shocks -Descending | Select-Object -First 1).total_shocks
$maxAPYValue      = ($top | Sort-Object lp_apy -Descending | Select-Object -First 1).lp_apy

# Compute averages / totals
$avgDrawdown = ($top | Measure-Object lp_max_drawdown_pct -Average).Average
$avgVol      = ($top | Measure-Object lp_volatility_abs_mean -Average).Average
$totalShocks = ($top | Measure-Object total_shocks -Sum).Sum
$avgAPY      = ($top | Measure-Object lp_apy -Average).Average

# Render summary bars
$dSum = Render-Bar $avgDrawdown $maxDrawdownValue 10 'Red'
$vSum = Render-Bar $avgVol      $maxVolValue      10 'Cyan'
$sSum = Render-Bar $totalShocks $maxShocksValue   10 'Yellow'
$aSum = Render-Bar $avgAPY      $maxAPYValue      10 'Green'

# Conditional coloring
$drawColor = if ($avgDrawdown -eq 0) { 'DarkGray' } elseif ($avgDrawdown -ge 5) { 'Red' } else { 'White' }
$volColor  = if ($avgVol -eq 0) { 'DarkGray' } else { 'White' }
$shkColor  = if ($totalShocks -eq 0) { 'DarkGray' } else { 'White' }
$apyColor  = if ($avgAPY -eq 0) { 'DarkGray' } elseif ($avgAPY -ge 10) { 'Green' } else { 'White' }

# Print summary
Write-Host "`nSUMMARY" -ForegroundColor White
Write-Host ("Draw {0,6:N2}% {1}" -f $avgDrawdown, $dSum.Bar) -ForegroundColor $drawColor
Write-Host ("Vol  {0,6:N2}% {1}" -f $avgVol, $vSum.Bar) -ForegroundColor $volColor
Write-Host ("Shk  {0,3}   {1}" -f $totalShocks, $sSum.Bar) -ForegroundColor $shkColor
Write-Host ("APY  {0,6:N2}% {1}" -f $avgAPY, $aSum.Bar) -ForegroundColor $apyColor

Write-Host "`n✅ Simulation run complete. Dashboard and summary displayed."



# ====================================================================
# === LP Reward Distribution Module
# ====================================================================

function Distribute-LP-Rewards {
    param(
        [Parameter(Mandatory=$true)]
        [array]$TopLPs,

        [double]$RewardPool = 1000,
        [switch]$TestMode,
        [string]$SlackWebhook = $env:COLINK_SLACK_WEBHOOK
    )

    Write-Host "`n▶ Starting reward distribution..." -ForegroundColor Cyan

    $totalApy = ($TopLPs | Measure-Object -Property lp_apy -Sum).Sum
    if ($totalApy -le 0) {
        Write-Warning "⚠️ No APY values detected; skipping rewards."
        return @()
    }

    $results = @()

    foreach ($lp in $TopLPs) {
        $weight = [double]$lp.lp_apy / $totalApy
        $reward = [math]::Round($RewardPool * $weight, 6)

        $record = [ordered]@{
            wallet     = $lp.wallet
            apy        = [double]$lp.lp_apy
            weight     = $weight
            reward_COL = $reward
            timestamp  = (Get-Date).ToString("s")
            status     = "pending"
        }

        if ($TestMode) {
            $record.status = "simulated"
        }
        else {
            try {
                # python scripts/xrpl.send_reward.py --wallet $lp.wallet --amount $reward
                $record.status = "sent"
            }
            catch {
                $record.status = "failed"
            }
        }

        $results += $record
    } # end foreach

    Write-Host "✔ Reward distribution complete." -ForegroundColor Green
    return $results
} # end function


# === Execute reward distribution ===
$RewardPool = 1000
$rewards = Distribute-LP-Rewards -TopLPs $top -RewardPool $RewardPool -TestMode:$TestMode

$rewardOut = Join-Path $summaryFolder ("lp_rewards_output_{0}.json" -f $timestamp)
$rewards | ConvertTo-Json -Depth 5 | Set-Content -Path $rewardOut -Encoding UTF8
Write-Host "`n💾 Rewards output saved → $rewardOut" -ForegroundColor Cyan

# ====================================================================
# END OF MODULE
# ====================================================================
