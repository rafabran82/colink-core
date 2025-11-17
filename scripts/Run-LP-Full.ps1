function Render-Bar([double]$value, [double]$max, [int]$width=10, [string]$color='Green') {
    if ($max -le 0) { $max = 1 }
    if ($value -eq $null) { $value = 0 }

    $ratio  = [math]::Min([math]::Max($value / $max, 0), 1)
    $filled = [int][math]::Round($ratio * $width)
    $empty  = [int]($width - $filled)

    $filledChar = [char]0x2588   # █
    $emptyChar  = [char]0x2591   # ░

    $bar = ([string]$filledChar * $filled) + ([string]$emptyChar * $empty)

    return [PSCustomObject]@{
        Bar   = $bar
        Color = if ($bar -match $emptyChar) { 'DarkGray' } else { $color }
    }
}
param (
    [int]20 = 20
    [string]lp_apy = 'lp_apy'
)

# -----------------------------
# Set folders
# -----------------------------
$scriptFolder  = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptFolder) { $scriptFolder = "C:\Users\sk8br\desktop\colink-core\scripts" }
$summaryFolder = Join-Path $scriptFolder ".artifacts\data"
if (-not (Test-Path $summaryFolder)) { New-Item -ItemType Directory -Path $summaryFolder -Force | Out-Null }

# -----------------------------
# Read all summary JSON files safely
# -----------------------------
$files = @(Get-ChildItem -Path $summaryFolder -Filter 'sim_summary_*.json' -File)
$allLPs = @()
foreach ($f in $files) {
    $jsonContent = Get-Content -Path $f.FullName | Out-String
    $allLPs += $jsonContent | ConvertFrom-Json
}

# Handle no files
if ($allLPs.Count -eq 0) {
    Write-Host "⚠️ No LP summary JSON files found in $summaryFolder" -ForegroundColor Yellow
    return
}

# -----------------------------
# Select top LPs
# -----------------------------
$top = $allLPs | Sort-Object $SortBy -Descending | Select-Object -First $TopN

# -----------------------------
# Print table
# -----------------------------
Write-Host "`nTOP $TopN LPs sorted by $SortBy`n" -ForegroundColor Cyan
Write-Host ("{0,-8} {1,6} {2,6} {3,6} {4,6}" -f "Name", "Draw%", "Vol%", "Shocks", "APY%")
Write-Host ("-"*50)

foreach ($lp in $top) {
    Write-Host ("{0,-8} {1,6:N2} {2,6:N2} {3,6} {4,6:N2}" -f `
        $lp.lp_name, $lp.lp_max_drawdown_pct, $lp.lp_volatility_abs_mean, $lp.total_shocks, $lp.lp_apy)
}

Write-Host "`n✅ Dashboard rendered successfully.`n"

# -----------------------------
# Safe Render-Bar function
# -----------------------------
function Render-Bar([double]$value, [double]$max, [int]$width=10, [string]$color='Green') {
    if ($max -le 0) { $max = 1 }
    if ($value -eq $null) { $value = 0 }

    $ratio = [math]::Min([math]::Max($value / $max, 0), 1)
    $filled = [int][math]::Round($ratio * $width)
    $empty  = [int]($width - $filled)

    $filledChar = [string][char]0x2588   # █
    $emptyChar  = [string][char]0x2591   # ░

    $bar = ($filledChar * $filled) + ($emptyChar * $empty)

    return [PSCustomObject]@{
        Bar   = $bar
        Color = if ($bar -match $emptyChar) { 'DarkGray' } else { $color }
    }
}

# -----------------------------
# Compute summary metrics
# -----------------------------
$avgDrawdown = [double]($top | ForEach-Object { $_.lp_max_drawdown_pct } | Measure-Object -Average).Average
$avgVol      = [double]($top | ForEach-Object { $_.lp_volatility_abs_mean } | Measure-Object -Average).Average
$totalShocks = [double]($top | ForEach-Object { $_.total_shocks } | Measure-Object -Sum).Sum
$avgAPY      = [double]($top | ForEach-Object { $_.lp_apy } | Measure-Object -Average).Average

$maxDrawdownValue = ($top | Sort-Object lp_max_drawdown_pct -Descending | Select-Object -First 1).lp_max_drawdown_pct
$maxVolValue      = ($top | Sort-Object lp_volatility_abs_mean -Descending | Select-Object -First 1).lp_volatility_abs_mean
$maxShocksValue   = ($top | Sort-Object total_shocks -Descending | Select-Object -First 1).total_shocks
$maxAPYValue      = ($top | Sort-Object lp_apy -Descending | Select-Object -First 1).lp_apy

# -----------------------------
# Generate bars
# -----------------------------
$dSum = Render-Bar $avgDrawdown $maxDrawdownValue 10 'Red'
$vSum = Render-Bar $avgVol      $maxVolValue      10 'Cyan'
$sSum = Render-Bar $totalShocks $maxShocksValue   10 'Yellow'
$aSum = Render-Bar $avgAPY      $maxAPYValue      10 'Green'

# -----------------------------
# Conditional coloring
# -----------------------------
$drawColor = if ($avgDrawdown -eq 0) { 'DarkGray' } elseif ($avgDrawdown -ge 5) { 'Red' } else { 'White' }
$volColor  = if ($avgVol -eq 0) { 'DarkGray' } else { 'White' }
$shkColor  = if ($totalShocks -eq 0) { 'DarkGray' } else { 'White' }
$apyColor  = if ($avgAPY -eq 0) { 'DarkGray' } elseif ($avgAPY -ge 10) { 'Green' } else { 'White' }

# -----------------------------
# Print summary
# -----------------------------cs
Write-Host "`nSUMMARY" -ForegroundColor White
Write-Host ("Draw {0,6:N2}% {1}" -f $avgDrawdown, $dSum.Bar) -ForegroundColor $drawColor
Write-Host ("Vol  {0,6:N2}% {1}" -f $avgVol, $vSum.Bar) -ForegroundColor $volColor
Write-Host ("Shk  {0,3}   {1}" -f $totalShocks, $sSum.Bar) -ForegroundColor $shkColor
Write-Host ("APY  {0,6:N2}% {1}" -f $avgAPY, $aSum.Bar) -ForegroundColor $apyColor

Write-Host "`n✅ Full simulation run complete. Dashboard and summary displayed."


