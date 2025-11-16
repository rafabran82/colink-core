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
# ============================
# LAYER 7 — REWARD DISPLAY
# ============================

function Get-LP-LatestRewardFile {
    param([string]$Dir)

    $files = Get-ChildItem -Path $Dir -Filter "lp_rewards_*.json" -ErrorAction SilentlyContinue
    if (-not $files) { return $null }

    $latest = $files | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    return $latest.FullName
}

function Show-LP-Rewards {
    param([Parameter(Mandatory=$true)][string]$RewardFile)

    try {
        $json = Get-Content $RewardFile -Raw | ConvertFrom-Json
        Write-Host "=== LATEST LP REWARDS ===" -ForegroundColor Cyan
        Write-Host ("Total Rewards: {0}" -f $json.TotalRewards)
        Write-Host ("Top Beneficiary: {0}" -f $json.TopBeneficiary)
        Write-Host ("RewardPool: {0}" -f $json.RewardPool)
    }
    catch {
        Write-Warning "⚠️ Could not parse rewards file: $RewardFile"
    }
}
# ============================
# LAYER 7 — REWARD DISPLAY (FIXED)
# Robust JSON parser
# ============================

function Show-LP-Rewards {
    param([Parameter(Mandatory=$true)][string]$RewardFile)

    try {
        $raw = Get-Content $RewardFile -Raw
        $json = $raw | ConvertFrom-Json -ErrorAction Stop

        Write-Host "=== LATEST LP REWARDS ===" -ForegroundColor Cyan

        if ($json -is [array]) {
            $total = ($json | Measure-Object amount -Sum).Sum
            $top   = $json | Sort-Object amount -Descending | Select-Object -First 1

            Write-Host ("Reward entries: {0}" -f $json.Count)
            Write-Host ("Total Rewards: {0}" -f $total)
            Write-Host ("Top Beneficiary: {0} ({1})" -f $top.lp, $top.amount)
        }
        else {
            # generic object-mode fallbacks
            Write-Host ("RewardPool: {0}" -f $json.RewardPool)
            Write-Host ("TotalRewards: {0}" -f $json.TotalRewards)
            Write-Host ("TopBeneficiary: {0}" -f $json.TopBeneficiary)
        }
    }
    catch {
        Write-Warning "⚠️ Could not parse rewards file: $RewardFile"
        Write-Warning $_.Exception.Message
    }
}
