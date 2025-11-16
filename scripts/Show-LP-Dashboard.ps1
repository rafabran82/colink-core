# ============================
# LAYER 7 — UNIVERSAL REWARD DISPLAY (BULLETPROOF)
# ============================

function Show-LP-Rewards {
    param([Parameter(Mandatory=$true)][string]$RewardFile)

    Write-Host "=== LATEST LP REWARDS ===" -ForegroundColor Cyan

    if (-not (Test-Path $RewardFile)) {
        Write-Warning "⚠️ Reward file missing: $RewardFile"
        return
    }

    try {
        $raw  = Get-Content $RewardFile -Raw
        $json = $raw | ConvertFrom-Json -Depth 10 -ErrorAction Stop
    }
    catch {
        Write-Warning "⚠️ Could not parse rewards file: $RewardFile"
        Write-Warning $_.Exception.Message
        return
    }

    # --- Case 1: Array of reward entries ---
    if ($json -is [array]) {
        if ($json.Count -eq 0) {
            Write-Host "No rewards."
            return
        }

        $total = ($json | Measure-Object amount -Sum).Sum
        $top   = $json | Sort-Object amount -Descending | Select-Object -First 1

        Write-Host ("Reward entries: {0}" -f $json.Count)
        Write-Host ("Total Rewards: {0}"   -f $total)
        Write-Host ("Top Beneficiary: {0} ({1})" -f $top.lp, $top.amount)
        return
    }

    # --- Case 2: Object with known keys ---
    $props = $json | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

    if ($props -contains "rewards") {
        $arr = $json.rewards
        if ($arr -is [array] -and $arr.Count -gt 0) {
            $total = ($arr | Measure-Object amount -Sum).Sum
            $top   = $arr | Sort-Object amount -Descending | Select-Object -First 1

            Write-Host ("Reward entries: {0}" -f $arr.Count)
            Write-Host ("Total Rewards: {0}"   -f $total)
            Write-Host ("Top Beneficiary: {0} ({1})" -f $top.lp, $top.amount)
            return
        }
    }

    # --- Generic fallback ---
    Write-Host "Raw Reward JSON:" -ForegroundColor DarkGray
    $json | ConvertTo-Json -Depth 10
}
