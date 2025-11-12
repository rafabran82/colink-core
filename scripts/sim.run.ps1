# --- COLINK Simulation Runner (final stable version) ---

Set-Location $PSScriptRoot

# --- 1. Pre-run: Python syntax guard ---
. (Join-Path $PSScriptRoot "ci.guard-python.ps1")
Invoke-PythonSyntaxGuard -Root (Split-Path $PSScriptRoot -Parent) -Include @("*.py") -Exclude @("\\.venv\\","\\.artifacts\\","\\_github\.off\\")

# --- 2. Prepare output directory ---
$repoRoot = Split-Path $PSScriptRoot -Parent
$timestamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")
$outDir = Join-Path $repoRoot ".artifacts\data\$timestamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Write-Host "📂 Output folder: $outDir"

# --- 3. Run simulation with proper arguments ---
$pyScript = Join-Path $repoRoot "scripts\sim.run.py"
if (-not (Test-Path $pyScript)) {
    Write-Error "❌ sim.run.py not found at $pyScript"
    exit 1
}

Write-Host "🐍 Executing Python simulation at: $pyScript"
& python "$pyScript" --out "$outDir"
if ($LASTEXITCODE -ne 0) {
    throw "sim.run.py failed with exit $LASTEXITCODE"
}

# --- 4. Post-run summary validation ---
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

# --- 5. Refresh dashboard ---
Write-Host "🔄 Refreshing dashboard..."
cmd /c (Join-Path $repoRoot "rebuild_ci.cmd")
Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd." -ForegroundColor Green


