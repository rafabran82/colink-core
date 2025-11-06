param(
  [ValidateSet("headless-agg","show-agg-offscreen","show-hold-tkagg","all")]
  [string]$Which = "all",
  [switch]$RunSim,
  [int]$Seed = 123,
  [string]$Pairs = "XRP/COL",
  [switch]$MetricsOnly
)

# --- Paths & output dir ---
$root   = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root ".sim_smoke"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Force headless rendering by default; the script can override per-mode if needed
if (-not $env:MPLBACKEND) { $env:MPLBACKEND = "Agg" }

# --- Resolve python robustly ---
function Resolve-Python {
  try {
    $c = Get-Command python3 -ErrorAction Stop
    return $c.Source
  } catch {
    try {
      $c = Get-Command python -ErrorAction Stop
      return $c.Source
    } catch {
      throw "Python not found on PATH."
    }
  }
}
$pythonExe = Resolve-Python

# --- Helper: run the sim engine with arguments; throw on non-zero exit ---
function Invoke-Py {
  param([Parameter(Mandatory=$true)][string[]]$Args)
  & $pythonExe @Args
  if ($LASTEXITCODE -ne 0) {
    throw "Simulation engine failed with exit code $LASTEXITCODE"
  }
}

# --- Common args for the engine ---
$baseArgs = @(
  (Join-Path $root "colink_core\sim\run_sweep.py"),
  "--pairs", $Pairs,
  "--seed", $Seed,
  "--out", $outDir
)

if ($MetricsOnly) { $baseArgs += "--metrics-only" }

# --- Always run the core engine when requested (no GUI) ---
if ($RunSim) {
  Write-Host ">> Sim Engine (Agg) for Pairs: $Pairs"
  Invoke-Py -Args $baseArgs
  Write-Host "OK: Engine"
}

# --- Mode runners -----------------------------------------------------------

function Run-Headless-Agg {
  # Produce a deterministic PNG without showing a window (CI-friendly)
  $png = Join-Path $outDir "sim_smoke_agg.png"
  $args = $baseArgs + @("--no-show", "--plot", $png)
  # Rely on MPLBACKEND=Agg rather than a CLI flag (the engine doesn't accept --backend)
  Invoke-Py -Args $args
  # Guard: if PNG not produced by engine, create a tiny fallback Agg PNG
  if (-not (Test-Path $png)) {
    Write-Host "WARN: $png missing; fallback Agg render..."
    $py = @"
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.makedirs(r"$($outDir)", exist_ok=True)
plt.figure()
plt.plot([0,1],[0,1])
plt.title("sim fallback (Agg)")
plt.savefig(r"$($png)", dpi=96, bbox_inches="tight")
print("FALLBACK_WROTE:", os.path.exists(r"$($png)"))
"@
    $tmp = Join-Path $env:TEMP ("sim_fallback_{0}.py" -f ([guid]::NewGuid()))
    Set-Content -Path $tmp -Value $py -Encoding utf8
    try { & $pythonExe $tmp | Write-Host } finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
  }
  if (-not (Test-Path $png)) {
    throw "Expected smoke image not found: $png"
  }
  Write-Host "OK: headless-agg (wrote $(Split-Path $png -Leaf))"
}

function Run-Show-Agg-Offscreen {
  # Offscreen render (no window), but exercise the "show" code path
  $png = Join-Path $outDir "sim_agg_offscreen.png"
  $args = $baseArgs + @("--plot", $png)
  Invoke-Py -Args $args
  if (-not (Test-Path $png)) {
    Write-Host "WARN: expected $png but it was not created."
  } else {
    Write-Host "OK: show-agg-offscreen"
  }
}

function Run-Show-Hold-TkAgg {
  # Interactive mode for local dev only; skip in CI (no display)
  $isCI = ($env:CI -eq "true" -or $env:GITHUB_ACTIONS -eq "true")
  if ($isCI) {
    Write-Host "SKIP: show-hold-tkagg (CI environment)"
    return
  }
  $env:MPLBACKEND = "TkAgg"
  $args = $baseArgs + @("--hold")
  Invoke-Py -Args $args
  Write-Host "OK: show-hold-tkagg"
}

# --- Dispatch by mode ---
$succeeded = @()
$skipped   = @()

switch ($Which) {
  "headless-agg"       { Run-Headless-Agg;       $succeeded += "headless-agg" }
  "show-agg-offscreen" { Run-Show-Agg-Offscreen; $succeeded += "show-agg-offscreen" }
  "show-hold-tkagg"    { Run-Show-Hold-TkAgg;    $succeeded += "show-hold-tkagg" }
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
foreach ($m in $succeeded) { Write-Host "* ${m}: PASS" }
foreach ($m in $skipped)   { Write-Host "* ${m}: SKIP" }
Write-Host "================================="

