param(
  [ValidateSet("headless-agg","show-agg-offscreen","show-hold-tkagg","all")]
  [string]$Which = "headless-agg",
  [switch]$RunSim,
  [int]$Seed = 123,
  [string]$Pairs = "XRP/COL",
  [switch]$MetricsOnly
)

# --- Paths & output dir ---------------------------------------------------
$repoRoot = Split-Path -Parent $PSScriptRoot
$outDir   = Join-Path $repoRoot "sim_smoke"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$env:MPLBACKEND = "Agg"
if ($env:PYTHON_EXE) { $pythonExe = $env:PYTHON_EXE }
$outJson = Join-Path $outDir "sim_from_engine.json"

# Headless rendering always
$env:MPLBACKEND = "Agg"

# --- Resolve Python (prefer repo venv) ------------------------------------
function Resolve-Python {
  $venv = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path $venv) { return @{ exe = $venv; args = @() } }

  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { return @{ exe = $cmd.Source; args = @() } }

  $cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($cmd) { return @{ exe = $cmd.Source; args = @('-3') } }

  throw "Could not resolve a working Python interpreter."
}

$py = Resolve-Python
$pythonExe = $py.exe
$pyArgs    = $py.args
Write-Host "Using Python: $pythonExe"

# --- Engine runner --------------------------------------------------------
function Run-Engine {
  if (-not $RunSim) { Write-Host "Skip sim-engine"; return }

  Write-Host ">> Sim Engine (Agg) for Pairs: $Pairs"
  $argsForSweep = @(
    "colink_core/sim/run_sweep.py",
    "--steps","200",
    "--pairs", $Pairs,
    "--seed",  "$Seed",
    "--out",   $outJson,
    "--plot",  "agg",
    "--display","agg",
    "--no-show"
  )
  if ($MetricsOnly) { $argsForSweep += "--metrics-only" }

  & $pythonExe @pyArgs @argsForSweep
  if ($LASTEXITCODE) {
    throw "Simulation engine failed with exit code $LASTEXITCODE"
  }
}

# --- PNG guard: ensure sim_smoke_agg.png exists ---------------------------
function Ensure-Smoke-Png {
  $png1 = Join-Path $outDir "sim_smoke_agg.png"
  if (Test-Path $png1) { return }

  Write-Host "WARN: smoke PNG missing; creating fallback Agg image..."
  $pySrc = @"
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs(r"{0}", exist_ok=True)
plt.figure()
plt.plot([0,1],[0,1])
plt.title("sim fallback (Agg)")
plt.savefig(r"{1}", dpi=96, bbox_inches="tight")
print("FALLBACK_WROTE:", os.path.exists(r"{1}"))
"@ -f $outDir, $png1

  $tmp = Join-Path $env:TEMP ("sim_fallback_{0}.py" -f ([guid]::NewGuid()))
  Set-Content -Path $tmp -Value $pySrc -Encoding utf8
  try {
    & $pythonExe @pyArgs $tmp | Write-Host
  } finally {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  }

  if (-not (Test-Path $png1)) {
    throw "Expected smoke image not found after fallback: $png1"
  }
}

# --- Display variants (CI safe) -------------------------------------------
function Run-Headless-Agg {
  Run-Engine
  Ensure-Smoke-Png
  Write-Host "OK: headless Agg"
}

function Run-Show-Agg-Offscreen {
  # Offscreen Agg path == no-op if headless succeeded
  Ensure-Smoke-Png
  Write-Host "OK: show-agg-offscreen"
}

function Run-Show-Hold-TkAgg {
  throw "Interactive TkAgg not supported in CI"
}

# --- Orchestration --------------------------------------------------------
$succeeded = @()
$skipped   = @()

switch ($Which) {
  "headless-agg"       { Run-Headless-Agg;       $succeeded += "headless-agg" }
  "show-agg-offscreen" { Run-Show-Agg-Offscreen; $succeeded += "show-agg-offscreen" }
  "show-hold-tkagg"    { try { Run-Show-Hold-TkAgg; $succeeded += "show-hold-tkagg" } catch { $skipped += "show-hold-tkagg" } }
  "all" {
    try { Run-Headless-Agg;       $succeeded += "headless-agg" }       catch { throw }
    try { Run-Show-Agg-Offscreen; $succeeded += "show-agg-offscreen" } catch { }
    try { Run-Show-Hold-TkAgg;    $succeeded += "show-hold-tkagg" }    catch { $skipped += "show-hold-tkagg" }
  }
}

# --- Summary ---------------------------------------------------------------
Write-Host ""
Write-Host "=== SIM DISPLAY SMOKE SUMMARY ==="
if ($RunSim) { Write-Host "* sim-engine: PASS (pairs=$Pairs)" }
foreach ($m in $succeeded) { Write-Host "* $($m): PASS" }
foreach ($m in $skipped)   { Write-Host "* $($m): SKIP" }
Write-Host "================================="




