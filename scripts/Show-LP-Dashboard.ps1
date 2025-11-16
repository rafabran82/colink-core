# ============================
# Show-LP-Dashboard.ps1
# ============================

# 1) Find latest CSV
$csvPath = Get-ChildItem ".artifacts/data/sim_summary_table.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $csvPath) { Write-Host "No CSV found!" -ForegroundColor Red; return }

# 2) Import CSV
$summary = Import-Csv $csvPath.FullName

# 3) Convert key fields to [double] for calculations
foreach ($row in $summary) {
    $row.lp_volatility_abs_mean = if ($row.lp_volatility_abs_mean -ne '') {[double]$row.lp_volatility_abs_mean} else {0}
    $row.total_shocks = if ($row.total_shocks -ne '') {[double]$row.total_shocks} else {0}
    $row.lp_max_drawdown_pct = if ($row.lp_max_drawdown_pct -ne '') {[double]$row.lp_max_drawdown_pct} else {0}
    $row.apy_realistic = if ($row.apy_realistic -ne '') {[double]$row.apy_realistic} else {0}
}

# 4) Sort top events by drawdown
$top = $summary | Sort-Object lp_max_drawdown_pct -Descending | Select-Object -First 20

# 5) Compute global maxima for sparklines
$maxVol = ($top | ForEach-Object {[double]$_.lp_volatility_abs_mean} | Measure-Object -Maximum).Maximum
$maxShocks = ($top | ForEach-Object {[double]$_.total_shocks} | Measure-Object -Maximum).Maximum

# 6) Helper: render mini-bar (sparkline)
function Render-Bar($value, $max, $length=10, $color='Green') {
    if ($max -eq 0) { $max = 1 }
    $filled = [math]::Round(($value / $max) * $length)
    $filled = [math]::Min($filled, $length)
    $empty = $length - $filled
    $bar = ('█' * $filled) + ('░' * $empty)
    return @{Bar=$bar; Color=$color}
}

# 7) Header
Write-Host ("{0,-20} {1,6} {2,8} {3,8} {4,6} {5,10} {6,10} {7,10} {8,10} {9,7}" -f `
    "Timestamp","Swaps","Vol","LPVal","DD%","VolBar","ShockBar","Shocks","APY","APYc") -ForegroundColor Cyan
Write-Host ("-" * 120) -ForegroundColor DarkGray

# 8) Display rows
foreach ($row in $top) {
    $volBarData = Render-Bar ([double]$row.lp_volatility_abs_mean) $maxVol 10 'Cyan'
    $shockBarData = Render-Bar ([double]$row.total_shocks) $maxShocks 10 (if([double]$row.total_shocks -gt 0) {'Yellow'} else {'Green'})

    $ddColor  = if ([double]$row.lp_max_drawdown_pct -ge 50) {'Red'} elseif ([double]$row.lp_max_drawdown_pct -ge 20) {'Yellow'} else {'Green'}
    $apyColor = if ([double]$row.apy_realistic -lt 0) {'Red'} elseif ([double]$row.apy_realistic -gt 2500) {'Magenta'} else {'Green'}

    Write-Host ("{0,-20} {1,6} {2,8:N2} {3,8:N0} {4,6:N1}" -f $row.timestamp,[double]$row.swaps_executed,[double]$row.total_volume,[double]$row.lp_total_value_user_final,[double]$row.lp_max_drawdown_pct) -ForegroundColor $ddColor -NoNewline
    Write-Host " " -NoNewline
    Write-Host $volBarData.Bar -ForegroundColor $volBarData.Color -NoNewline
    Write-Host " " -NoNewline
    Write-Host $shockBarData.Bar -ForegroundColor $shockBarData.Color -NoNewline
    Write-Host " " -NoNewline
    Write-Host ("{0,7:N2}" -f [double]$row.apy_realistic) -ForegroundColor $apyColor
}

Write-Host "`nDashboard rendered. Top LP events by drawdown, volatility, shocks, and APY." -ForegroundColor Green
