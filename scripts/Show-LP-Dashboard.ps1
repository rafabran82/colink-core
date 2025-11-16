# ---------------------------
# Show-LP-Dashboard.ps1
# ---------------------------

# 1) Load all summary JSONs safely
$summaryText = Get-Content ".artifacts/data/sim_summary_*.json" -Raw
$objects = $summaryText -split '}\s*\r?\n'
$summaryObjects = @()

foreach ($obj in $objects) {
    $trimmed = $obj.Trim()
    if ($trimmed -ne '') {
        try {
            $json = "$trimmed}"
            $summaryObjects += $json | ConvertFrom-Json
        } catch {
            # skip invalid fragments
        }
    }
}

# 2) Export to CSV
$summaryObjects | Export-Csv ".artifacts/data/sim_summary_table.csv" -NoTypeInformation

# 3) Load CSV
$summary = Import-Csv ".artifacts/data/sim_summary_table.csv"

# 4) Ensure numeric columns are doubles
$summary | ForEach-Object {
    $_.lp_volatility_abs_mean = if ($_.lp_volatility_abs_mean -ne '') {[double]$_.lp_volatility_abs_mean} else {0}
    $_.total_shocks           = if ($_.total_shocks -ne '') {[double]$_.total_shocks} else {0}
    $_.lp_max_drawdown_pct    = if ($_.lp_max_drawdown_pct -ne '') {[double]$_.lp_max_drawdown_pct} else {0}
    $_.apy_realistic          = if ($_.apy_realistic -ne '') {[double]$_.apy_realistic} else {0}
}

# 5) Pick top 20 by max drawdown
$top = @($summary | Sort-Object lp_max_drawdown_pct -Descending | Select-Object -First 20)

# 6) Compute global maxima for sparklines
$maxVol      = ($top | ForEach-Object {[double]$_.lp_volatility_abs_mean} | Measure-Object -Maximum).Maximum
$maxShocks   = ($top | ForEach-Object {[double]$_.total_shocks}           | Measure-Object -Maximum).Maximum
$maxDrawdown = ($top | ForEach-Object {[double]$_.lp_max_drawdown_pct}   | Measure-Object -Maximum).Maximum
$maxAPY      = ($top | ForEach-Object {[double]$_.apy_realistic}         | Measure-Object -Maximum).Maximum

# 7) Mini-bar helper
function Render-Bar($value, $max, $length=10, $color='Green') {
    if ($max -eq 0) { $max = 1 }
    $filled = [math]::Round(($value / $max) * $length)
    $filled = [math]::Min($filled, $length)
    $empty  = $length - $filled
    $bar = ('█' * $filled) + ('░' * $empty)
    return @{Bar=$bar; Color=$color}
}

# 8) Header
Write-Host ("{0,-20} {1,6} {2,8} {3,8} {4,6} {5,10} {6,10} {7,10} {8,10} {9,7}" -f `
    "Timestamp","Swaps","Vol","LPVal","DD%","VolBar","ShockBar","Shocks","APY","APYc") -ForegroundColor Cyan
Write-Host ("-" * 120) -ForegroundColor DarkGray

# 9) Display each row
foreach ($row in $top) {
    $volBarData   = Render-Bar ([double]$row.lp_volatility_abs_mean) $maxVol 10 'Cyan'
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
