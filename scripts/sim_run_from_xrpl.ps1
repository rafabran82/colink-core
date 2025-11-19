param(
    [string]$Label = "SIM-FROM-XRPL"
)

Write-Host "▶ Running Simulation from XRPL State (Label: $Label)..." -ForegroundColor Cyan

# --- Load XRPL snapshot
$state = ".artifacts/sim/sim_state.json"
if (-not (Test-Path $state)) {
    Write-Host "❌ Missing sim_state.json — run XRPL-Snapshot-State first!" -ForegroundColor Red
    exit 1
}

# --- Create run directory
$runDir = Join-Path ".artifacts/sim/runs" (Get-Date -Format "yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Path $runDir | Out-Null
Write-Host "ℹ️ Using run directory: $runDir" -ForegroundColor Yellow

# --- Pick simulator automatically
$simPy = Join-Path (Get-Location) "scripts/sim.run.py"
$simPS = Join-Path (Get-Location) "scripts/sim.run.ps1"

if (Test-Path $simPy) {
    Write-Host "ℹ️ Using Python simulator: $simPy" -ForegroundColor Yellow
    $cmd = "python `"$simPy`" --input `"$state`" --output `"$runDir/sim_output.json`" --meta `"$runDir/meta.json`""
    & python $simPy --input $state --output "$runDir/sim_output.json" --meta "$runDir/meta.json" 2>&1 |
        ForEach-Object { Write-Host "   $_" }
}
elseif (Test-Path $simPS) {
    Write-Host "ℹ️ Using PowerShell simulator: $simPS" -ForegroundColor Yellow
    & $simPS -Input $state -Output "$runDir/sim_output.json" -Meta "$runDir/meta.json"
}
else {
    Write-Host "❌ No simulator found (sim.run.py or sim.run.ps1 missing)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🟢 Simulation complete" -ForegroundColor Green
Write-Host "📦 Output: $runDir"
Write-Host ""
Write-Host "—— sim_run_from_xrpl Completed ——"

