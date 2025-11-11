# --- COLINK Simulation Runner (stable cross-version edition) ---

# Move to scripts directory (where this file lives)
Set-Location $PSScriptRoot

# --- 1. Pre-run: Python syntax guard ---
. (Join-Path $PSScriptRoot "ci.guard-python.ps1")
Invoke-PythonSyntaxGuard -Root "scripts" -Include @("*.py")

# --- 2. Run simulation using absolute path ---
$repoRoot = Split-Path $PSScriptRoot -Parent
$pyScript = Join-Path $repoRoot "scripts\sim.run.py"

if (-not (Test-Path $pyScript)) {
    Write-Error "❌ sim.run.py not found at $pyScript"
    exit 1
}

Write-Host "🐍 Executing Python simulation at: $pyScript"
& python "$pyScript"
if ($LASTEXITCODE -ne 0) {
    throw "sim.run.py failed with exit $LASTEXITCODE"
}

# --- 3. Post-run: summary validation guard ---
$guardPath = Join-Path $PSScriptRoot "ci.guard-summary.ps1"
if (-not (Test-Path $guardPath)) {
    Write-Warning "⚠️ Guard script not found at $guardPath — skipping validation."
}
else {
    try {
        $guardResult = & $guardPath
        $exitCode = if (Test-Path variable:LASTEXITCODE) { $LASTEXITCODE } else { 0 }
        if ($exitCode -ne 0 -or $guardResult -ne 0) {
            Write-Warning "⚠️ Summary validation failed — dashboard refresh skipped."
            return
        }
        else {
            Write-Host "✅ Summary validation succeeded — continuing to dashboard refresh." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ Error invoking guard script: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# --- 4. Refresh dashboard ---
Write-Host "🔄 Refreshing dashboard..."
cmd /c rebuild_ci.cmd
Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd." -ForegroundColor Green
