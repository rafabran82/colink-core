param (
    [int]$TopN = 20,
    [string]$SortBy = 'lp_apy'
)

# Ensure LP data exists
if (-not (Get-Variable -Name lpObjects -Scope 0 -ErrorAction SilentlyContinue)) {
    $lpObjects = @(
        [PSCustomObject]@{ lp_name='LP-A'; lp_max_drawdown_pct=5.2; lp_volatility_abs_mean=2.1; total_shocks=3; lp_apy=12.5 }
        [PSCustomObject]@{ lp_name='LP-B'; lp_max_drawdown_pct=0; lp_volatility_abs_mean=0; total_shocks=0; lp_apy=0 }
        [PSCustomObject]@{ lp_name='LP-C'; lp_max_drawdown_pct=7.8; lp_volatility_abs_mean=3.4; total_shocks=5; lp_apy=8.9 }
    )
}

# Top N LPs
$top = $lpObjects | Sort-Object $SortBy -Descending | Select-Object -First $TopN

# Max values for bars
$maxDrawdownValue = ($top | Sort-Object lp_max_drawdown_pct -Descending | Select-Object -First 1).lp_max_drawdown_pct
$maxVolValue      = ($top | Sort-Object lp_volatility_abs_mean -Descending | Select-Object -First 1).lp_volatility_abs_mean
$maxShocksValue   = ($top | Sort-Object total_shocks -Descending | Select-Object -First 1).total_shocks
$maxAPYValue      = ($top | Sort-Object lp_apy -Descending | Select-Object -First 1).lp_apy

# Render-Bar function
function Render-Bar($value,$max,$width=10,$color='Green') {
    $max   = if ($max -gt 0) { $max } else { 1 }
    $value = if ($value -eq $null) { 0 } else { $value }
    $filled = [math]::Round([math]::Min([math]::Max($value/$max,0),1)*$width)
    $empty  = $width - $filled
    $bar = ('█'* $filled) + ('░'* $empty)
    [PSCustomObject]@{ Bar=$bar; Color=if($bar -match '░'){ 'DarkGray' } else { $color } }
}

# Display dashboard
$dashboardPath = ".\Show-LP-Dashboard.ps1"
if (Test-Path $dashboardPath) {
    . $dashboardPath -TopN $TopN -SortBy $SortBy
} else {
    Write-Host "❌ Dashboard script not found at $dashboardPath" -ForegroundColor Red
}

# Compute summary
$avgDrawdown = ($top | ForEach-Object { $_.lp_max_drawdown_pct } | Measure-Object -Average).Average
$avgVol      = ($top | ForEach-Object { $_.lp_volatility_abs_mean } | Measure-Object -Average).Average
$totalShocks = ($top | ForEach-Object { $_.total_shocks } | Measure-Object -Sum).Sum
$avgAPY      = ($top | ForEach-Object { $_.lp_apy } | Measure-Object -Average).Average

# Render bars
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
Write-Host "
SUMMARY" -ForegroundColor White
Write-Host ("Draw {0,6:N2}% {1}" -f $avgDrawdown, $dSum.Bar) -ForegroundColor $drawColor
Write-Host ("Vol  {0,6:N2}% {1}" -f $avgVol, $vSum.Bar) -ForegroundColor $volColor
Write-Host ("Shk  {0,3}   {1}" -f $totalShocks, $sSum.Bar) -ForegroundColor $shkColor
Write-Host ("APY  {0,6:N2}% {1}" -f $avgAPY, $aSum.Bar) -ForegroundColor $apyColor
Write-Host "
✅ Full simulation run complete. Dashboard and summary displayed."
