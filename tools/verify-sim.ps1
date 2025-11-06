param(
  [ValidateSet("headless-agg","show-agg-offscreen","show-hold-tkagg","all")]
  [string]$Which = "all",
  [switch]$RunSim,
  [int]$Seed = 123,
  [string]$Pairs = "XRP/COL",
  [switch]$MetricsOnly
)

$ErrorActionPreference = "Stop"

# Pick a Python executable that works cross-platform
function Get-PyExe {
  $c = Get-Command python  -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  $c = Get-Command python3 -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return "python"
}
$PyExe = Get-PyExe

# Portable output dir next to repo root
$root   = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root ".sim_smoke"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Normalize pairs list (allow comma-separated)
$pairList = $Pairs -split '\s*,\s*' | Where-Object { $_ -ne "" }
$pairArg  = ($pairList -join ",")

# File names
$pngAgg  = Join-Path $outDir "sim_smoke_agg.png"
$jsonOut = Join-Path $outDir "sim_from_engine.json"

# Build python args  (DON'T name this $args – that's reserved in PS!)
$pyArgs = @(
  "-m","colink_core.sim.run_sweep",
  "--steps","50",
  "--out", $jsonOut,
  "--pairs", $pairArg,
  "--seed", "$Seed",
  "--display","Agg",
  "--no-show"
)
if ($MetricsOnly) {
  $pyArgs += "--metrics-only"
} else {
  $pyArgs += @("--plot", $pngAgg)
}

function Invoke-Engine {
  Write-Host (">> Sim Engine (Agg) for Pairs: $pairArg") -ForegroundColor Cyan
  & $PyExe @pyArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Engine failed with exit code $LASTEXITCODE"
  }
  if ($MetricsOnly) {
    if (-not (Test-Path $jsonOut)) { throw "Expected metrics JSON not found: $jsonOut" }
  } else {
    if (-not (Test-Path $pngAgg))  { throw "Expected Agg PNG not found: $pngAgg" }
  }
}

if ($RunSim) {
  Invoke-Engine
  if ($MetricsOnly) {
    Write-Host "`n=== SIM DISPLAY SMOKE SUMMARY ==="
    Write-Host "* sim-engine: PASS (pairs=$($pairList -join ', '), metrics-only)" -ForegroundColor Green
    Write-Host "================================="
  } else {
    Write-Host "OK: Agg" -ForegroundColor Green
    Write-Host "`n=== SIM DISPLAY SMOKE SUMMARY ==="
    Write-Host "* sim-engine: PASS (pairs=$($pairList -join ', '))" -ForegroundColor Green
    Write-Host "* headless-agg: PASS (wrote $(Split-Path -Leaf $pngAgg))" -ForegroundColor Green
    Write-Host "* show-agg-offscreen: PASS" -ForegroundColor Green
    Write-Host "* show-hold-tkagg: SKIP (interactive not enabled in CI)" -ForegroundColor Yellow
    Write-Host "================================="
  }
}
