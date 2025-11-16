function Show-LP-Dashboard {
# [paste the full script content above here]

# -----------------------------
# Health Check Summary
# -----------------------------
$drawdownThreshold = 5
$volThreshold      = 5
$apyThreshold      = 10
$shocksThreshold   = 0

$issues = @()
if ($avgDrawdown -ge $drawdownThreshold) { $issues += "Drawdown high ($avgDrawdown%)" }
if ($avgVol -ge $volThreshold) { $issues += "Volatility high ($avgVol%)" }
if ($avgAPY -lt $apyThreshold) { $issues += "APY low ($avgAPY%)" }
if ($totalShocks -gt $shocksThreshold) { $issues += "Total shocks > 0 ($totalShocks)" }

$healthStatus = if ($issues.Count -gt 0) { "⚠️ Issues detected: " + ($issues -join "; ") } else { "✅ All metrics are within safe limits. Everything is GREEN!" }
Write-Host "`n📊 HEALTH CHECK: $healthStatus`n"

}
