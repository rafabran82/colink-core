param(
    [string]$Label = "PHASE3-DEFAULT"
)

# Sim Phase 3 Runner Helper
# - Thin wrapper around run_sim.ps1
# - No window-closing exits
# - Emoji health summary at the end

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "▶ Sim-Phase3-Run starting (Label: $Label)..." -ForegroundColor Cyan

try {
    $root = Split-Path $PSScriptRoot -Parent
    Set-Location $root

    $simScript = Join-Path $PSScriptRoot "run_sim.ps1"
    if (-not (Test-Path $simScript)) {
        Write-Host "❌ Unable to find run_sim.ps1 at: $simScript" -ForegroundColor Red
        Write-Host "🟠 Sim Phase 3: FAILED (missing base sim script)" -ForegroundColor Yellow
        return
    }

    Write-Host "ℹ️ Using base sim script: $simScript" -ForegroundColor DarkCyan
    Write-Host "⏱ Launching liquidity simulation..." -ForegroundColor Cyan

    # Call the existing sim runner; no assumptions on its flags yet
    & $simScript

    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Host "⚠️ run_sim.ps1 completed with code $exitCode" -ForegroundColor Yellow
        Write-Host "🟠 Sim Phase 3: ISSUES DETECTED (check run_sim output/logs)" -ForegroundColor Yellow
    }
    else {
        Write-Host "✅ run_sim.ps1 completed successfully." -ForegroundColor Green
        Write-Host "🟢 Sim Phase 3: OK (baseline run succeeded)" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Exception while running Phase 3 sim: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🟠 Sim Phase 3: FAILED (exception thrown)" -ForegroundColor Yellow
}
finally {
    Write-Host ""
    Write-Host "—— Sim-Phase3-Run completed (Label: $Label) ——" -ForegroundColor DarkGray
}
