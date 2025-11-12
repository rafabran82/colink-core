# COLINK Daily CI (clean single-flow)
param([switch]$Quiet)

$ErrorActionPreference = "Stop"

function Info([string]$msg)  { if (-not $Quiet) { Write-Host $msg } }
function Warn([string]$msg)  { Write-Warning $msg }
function Ok([string]$msg)    { if (-not $Quiet) { Write-Host $msg -ForegroundColor Green } }

# --- Paths ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot  = Split-Path $scriptDir -Parent

$artifactsDir = Join-Path $repoRoot ".artifacts"
$runsDir      = Join-Path $artifactsDir "data"
$indexPath    = Join-Path $artifactsDir "index.html"
$metricsDir   = Join-Path $artifactsDir "metrics"
$summaryJson  = Join-Path $metricsDir "summary.json"
$summaryCsv   = Join-Path $metricsDir "summary.csv"
$deltaJson    = Join-Path $metricsDir "delta.json"

# --- Start banner ---
Info "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate old runs (noop unless threshold exceeded) ---
if (-not (Test-Path $runsDir)) { New-Item -ItemType Directory -Force -Path $runsDir | Out-Null }
$keep = 100
$allRuns = Get-ChildItem -Directory $runsDir -ErrorAction SilentlyContinue | Sort-Object Name
$extra = [Math]::Max(0, ($allRuns.Count - $keep))
if ($extra -gt 0) {
  $allRuns | Select-Object -First $extra | Remove-Item -Recurse -Force
  Ok "♻️ Rotated $extra old runs (keep=$keep)."
} else {
  Ok "✅ Nothing to rotate ($($allRuns.Count) runs, keep=$keep)."
}

# --- Python guard (compile syntax of any *.py under scripts) ---
$pyRoot = Join-Path $repoRoot "scripts"
$pyFiles = Get-ChildItem -Recurse -File -Path $pyRoot -Include *.py -ErrorAction SilentlyContinue
if ($pyFiles.Count -gt 0) {
  Info "🔍 Python guard scanning root: $pyRoot"
  $errCount = 0
  foreach ($f in $pyFiles) {
    $out = & python -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) { $errCount++ ; Write-Warning "⚠️ Syntax error in $($f.Name): $out" }
  }
  if ($errCount -eq 0) { Ok "✅ Python lint check passed for all scripts." }
} else {
  Info "ℹ️  No Python files to lint under $pyRoot — skipping."
}

# --- Make a fresh output folder for the run ---
$stamp      = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir     = Join-Path $runsDir $stamp
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Ok "📂 Output folder: $outDir"

# --- Run the simulation (scripts\sim.run.py) ---
$simPy = Join-Path $pyRoot "sim.run.py"
if (Test-Path $simPy) {
  Info "🐍 Executing Python simulation at: $simPy"
  & python $simPy 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Simulation failed (exit $LASTEXITCODE)" }
} else {
  Warn "Simulation entry not found: $simPy"
}

# --- Minimal validation that metrics.json exists if the sim created it ---
$runMetrics = Join-Path $outDir "metrics.json"
if (Test-Path $runMetrics) {
  Ok "✅ Metrics written: $runMetrics"
} else {
  Warn "metrics.json not found in $outDir (sim may be a no-op for this run)."
}

# --- Rebuild dashboard if helper exists (should NOT open browser) ---
$rebuildCmd = Join-Path $repoRoot "rebuild_ci.cmd"
if (Test-Path $rebuildCmd) {
  Info "🔄 Refreshing dashboard..."
  & $rebuildCmd 2>&1 | ForEach-Object {
    # silence any 'echo Write-Host ...' lines that legacy scripts might print
    if ($_ -notmatch 'Write-Host') { $_ }
  }
  Ok "✅ Dashboard refreshed via rebuild_ci.cmd."
} else {
  Warn "rebuild_ci.cmd not found — skipping dashboard rebuild."
}

# --- Metrics summary/delta are produced by your build; just report if present ---
if (Test-Path $summaryJson) { Ok "✅ Metrics summary present: $summaryJson" }
if (Test-Path $summaryCsv)  { Ok "✅ Metrics summary CSV present: $summaryCsv" }
if (Test-Path $deltaJson)   { Ok "✅ Delta summary present:   $deltaJson" }

# --- Embed field-safe metrics badge (centralized) ---
$embedPath = Join-Path $scriptDir "ci.embed-latest.ps1"
if (Test-Path $embedPath) {
  & $embedPath -IndexPath $indexPath -SummaryJson $summaryJson -DeltaJson $deltaJson -Quiet
} else {
  Warn "Embed script not found: $embedPath"
}

# --- Open dashboard once (absolute path from repo root) ---
if (Test-Path $indexPath) {
  Start-Process $indexPath
  Write-Host "🌐 Dashboard opened: $indexPath"
} else {
  Warn "Dashboard not found: $indexPath"
}
