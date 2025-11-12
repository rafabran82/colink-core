# COLINK Daily CI — clean single-flow (robust sim launcher)
param([switch]$Quiet)
$ErrorActionPreference = "Stop"

function Info([string]$m){ if (-not $Quiet) { Write-Host $m } }
function Ok([string]$m){ if (-not $Quiet) { Write-Host $m -ForegroundColor Green } }
function Warn([string]$m){ Write-Warning $m }

# --- Paths
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot    = Split-Path $scriptDir -Parent
$artifacts   = Join-Path $repoRoot ".artifacts"
$runsDir     = Join-Path $artifacts "data"
$indexPath   = Join-Path $artifacts "index.html"
$metricsDir  = Join-Path $artifacts "metrics"
$summaryJson = Join-Path $metricsDir "summary.json"
$summaryCsv  = Join-Path $metricsDir "summary.csv"
$deltaJson   = Join-Path $metricsDir "delta.json"

# --- Start
Info "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate runs (keep=100)
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null
$keep = 100
$all  = Get-ChildItem -Directory $runsDir -ErrorAction SilentlyContinue | Sort-Object Name
$extra = [math]::Max(0, $all.Count - $keep)
if ($extra -gt 0) { $all | Select-Object -First $extra | Remove-Item -Recurse -Force ; Ok "♻️ Rotated $extra old runs (keep=$keep)." }
else { Ok "✅ Nothing to rotate ($($all.Count) runs, keep=$keep)." }

# --- Python guard (compile *.py under scripts)
$pyRoot = Join-Path $repoRoot "scripts"
$pyFiles = Get-ChildItem -Recurse -File -Path $pyRoot -Include *.py -ErrorAction SilentlyContinue
if ($pyFiles.Count -gt 0) {
  Info "🔍 Python guard scanning root: $pyRoot"
  $errs = 0
  foreach ($f in $pyFiles) {
    $out = & python -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) { $errs++ ; Write-Warning ("⚠️ Syntax error in {0}: {1}" -f $f.Name, $out) }
  }
  if ($errs -eq 0) { Ok "✅ Python lint check passed for all scripts." }
} else {
  Info ("ℹ️  No Python files to lint under {0} — skipping." -f $pyRoot)
}

# --- New run dir
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $runsDir $stamp
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Ok ("📂 Output folder: {0}" -f $outDir)

# --- Run simulation (robust launcher)
$simPy = Join-Path $pyRoot "sim.run.py"
if (Test-Path $simPy) {
  Info ("🐍 Executing Python simulation at: {0}" -f $simPy)

  # Always pass --out; try a few forms so we work with most CLIs
  $attempts = @(
    @{ label = 'array-args'; args = @('--out', $outDir) },
    @{ label = 'assign-out'; args = @("--out=$outDir") },
    @{ label = 'quoted-out'; args = @('--out', "$outDir") }
  )

  $runOk = $false
  foreach ($a in $attempts) {
    try {
      Write-Host ("# --- Simplified COLINK simulation runner (single safe attempt) ---
$simPy = "scripts/sim.run.py"
Write-Host "🐍 Executing Python simulation via $simPy ..."
try {
    $simOut = & python $simPy 2>&1
    if ($LASTEXITCODE -ne 0 -or ($simOut -match "Traceback|Error|Exception")) {
        Write-Warning "Simulation produced warnings or non-zero exit; see output below:"
        Write-Host $simOut
    } else {
        Write-Host "✅ Python simulation executed cleanly."
    }
} catch {
    Write-Warning "Simulation failed to execute: $(# COLINK Daily CI — clean single-flow (robust sim launcher)
param([switch]$Quiet)
$ErrorActionPreference = "Stop"

function Info([string]$m){ if (-not $Quiet) { Write-Host $m } }
function Ok([string]$m){ if (-not $Quiet) { Write-Host $m -ForegroundColor Green } }
function Warn([string]$m){ Write-Warning $m }

# --- Paths
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot    = Split-Path $scriptDir -Parent
$artifacts   = Join-Path $repoRoot ".artifacts"
$runsDir     = Join-Path $artifacts "data"
$indexPath   = Join-Path $artifacts "index.html"
$metricsDir  = Join-Path $artifacts "metrics"
$summaryJson = Join-Path $metricsDir "summary.json"
$summaryCsv  = Join-Path $metricsDir "summary.csv"
$deltaJson   = Join-Path $metricsDir "delta.json"

# --- Start
Info "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate runs (keep=100)
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null
$keep = 100
$all  = Get-ChildItem -Directory $runsDir -ErrorAction SilentlyContinue | Sort-Object Name
$extra = [math]::Max(0, $all.Count - $keep)
if ($extra -gt 0) { $all | Select-Object -First $extra | Remove-Item -Recurse -Force ; Ok "♻️ Rotated $extra old runs (keep=$keep)." }
else { Ok "✅ Nothing to rotate ($($all.Count) runs, keep=$keep)." }

# --- Python guard (compile *.py under scripts)
$pyRoot = Join-Path $repoRoot "scripts"
$pyFiles = Get-ChildItem -Recurse -File -Path $pyRoot -Include *.py -ErrorAction SilentlyContinue
if ($pyFiles.Count -gt 0) {
  Info "🔍 Python guard scanning root: $pyRoot"
  $errs = 0
  foreach ($f in $pyFiles) {
    $out = & python -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) { $errs++ ; Write-Warning ("⚠️ Syntax error in {0}: {1}" -f $f.Name, $out) }
  }
  if ($errs -eq 0) { Ok "✅ Python lint check passed for all scripts." }
} else {
  Info ("ℹ️  No Python files to lint under {0} — skipping." -f $pyRoot)
}

# --- New run dir
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $runsDir $stamp
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Ok ("📂 Output folder: {0}" -f $outDir)

# --- Run simulation (robust launcher)
$simPy = Join-Path $pyRoot "sim.run.py"
if (Test-Path $simPy) {
  Info ("🐍 Executing Python simulation at: {0}" -f $simPy)

  # Always pass --out; try a few forms so we work with most CLIs
  $attempts = @(
    @{ label = 'array-args'; args = @('--out', $outDir) },
    @{ label = 'assign-out'; args = @("--out=$outDir") },
    @{ label = 'quoted-out'; args = @('--out', "$outDir") }
  )

  $runOk = $false
  foreach ($a in $attempts) {
    try {
      Write-Host ("# --- Simulation block placeholder --- via rebuild_ci.cmd."
} else {
  Warn "rebuild_ci.cmd not found — skipping dashboard rebuild."
}

# --- Report summaries (if produced)
if (Test-Path $summaryJson) { Ok ("✅ Metrics summary JSON present: {0}" -f $summaryJson) }
if (Test-Path $summaryCsv)  { Ok ("✅ Metrics summary CSV present:  {0}" -f $summaryCsv) }
if (Test-Path $deltaJson)   { Ok ("✅ Delta summary present:       {0}" -f $deltaJson) }

# --- Embed metrics badge (centralized; Quiet)
$embedPath = Join-Path $scriptDir "ci.embed-latest.ps1"
if (Test-Path $embedPath) {
  & $embedPath -IndexPath $indexPath -SummaryJson $summaryJson -DeltaJson $deltaJson -Quiet
} else {
  Warn ("Embed script not found: {0}" -f $embedPath)
}

# --- Open dashboard once
if (Test-Path $indexPath) {
  Start-Process explorer.exe "/select,$IndexPath"
  Write-Host ("🌐 Dashboard opened: {0}" -f $indexPath)
} else {
  Warn ("Dashboard not found: {0}" -f $indexPath)
}

# --- Integrity guard: ensure exactly ONE embed + ONE open block are present in this file
try {
  $self = Get-Content $MyInvocation.MyCommand.Definition -Raw
  $rxEmb = '(?mi)^\s*\$embedPath\s*=\s*Join-Path\s+\$PSScriptRoot\s+"ci\.embed-latest\.ps1"[\s\S]*?^\s*&\s*\$embedPath\s+-Quiet\s*$'
  $rxOpen = '(?mi)^\s*if\s*\(Test-Path\s*\$indexPath\)\s*\{\s*Start-Process\s*\$indexPath[\s\S]*?Write-Host\s*"Dashboard opened:.*?$'
  $e = ([regex]::Matches($self, $rxEmb)).Count
  $o = ([regex]::Matches($self, $rxOpen)).Count
  if ($e -eq 1 -and $o -eq 1) {

  } else {
  }
} catch {
  Write-Warning ("Integrity guard failed: {0}" -f $_.Exception.Message)
}






.Exception.Message)"
}
# --- End simulation block --- via rebuild_ci.cmd."
} else {
  Warn "rebuild_ci.cmd not found — skipping dashboard rebuild."
}

# --- Report summaries (if produced)
if (Test-Path $summaryJson) { Ok ("✅ Metrics summary JSON present: {0}" -f $summaryJson) }
if (Test-Path $summaryCsv)  { Ok ("✅ Metrics summary CSV present:  {0}" -f $summaryCsv) }
if (Test-Path $deltaJson)   { Ok ("✅ Delta summary present:       {0}" -f $deltaJson) }

# --- Embed metrics badge (centralized; Quiet)
$embedPath = Join-Path $scriptDir "ci.embed-latest.ps1"
if (Test-Path $embedPath) {
  & $embedPath -IndexPath $indexPath -SummaryJson $summaryJson -DeltaJson $deltaJson -Quiet
} else {
  Warn ("Embed script not found: {0}" -f $embedPath)
}

# --- Open dashboard once
if (Test-Path $indexPath) {
  Start-Process explorer.exe "/select,$IndexPath"
  Write-Host ("🌐 Dashboard opened: {0}" -f $indexPath)
} else {
  Warn ("Dashboard not found: {0}" -f $indexPath)
}

# --- Integrity guard: ensure exactly ONE embed + ONE open block are present in this file
try {
  $self = Get-Content $MyInvocation.MyCommand.Definition -Raw
  $rxEmb = '(?mi)^\s*\$embedPath\s*=\s*Join-Path\s+\$PSScriptRoot\s+"ci\.embed-latest\.ps1"[\s\S]*?^\s*&\s*\$embedPath\s+-Quiet\s*$'
  $rxOpen = '(?mi)^\s*if\s*\(Test-Path\s*\$indexPath\)\s*\{\s*Start-Process\s*\$indexPath[\s\S]*?Write-Host\s*"Dashboard opened:.*?$'
  $e = ([regex]::Matches($self, $rxEmb)).Count
  $o = ([regex]::Matches($self, $rxOpen)).Count
  if ($e -eq 1 -and $o -eq 1) {

  } else {
  }
} catch {
  Write-Warning ("Integrity guard failed: {0}" -f $_.Exception.Message)
}











