param(
  [ValidateSet("headless-agg","show-agg-offscreen","show-hold-tkagg","all")$root  = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root ".sim_smoke"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null]
  [string]$Which = "all",
  [switch]$RunSim,
  [int]$Seed = 123,
  [string]$Pairs = "XRP/COL",
  [switch]$MetricsOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---- helpers ----
function New-Dir {
  param([Parameter(Mandatory=$true)][string]$Path)
  New-Item -ItemType Directory -Path $Path -Force | Out-Null
}
$root  = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root ".sim_smoke"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
try { New-Dir $OutDir } catch {}

# split pairs e.g. "XRP/COL,COPX/COL"
$pairList = $Pairs -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }

# sanitize pair to filename suffix (xrp-col)
function Pair-Suffix([string]$p) {
  $p.ToLower().Replace('/','-')
}

# ---- smoke: headless agg (no external sim_plot.py dependency) ----
function Run-HeadlessAgg {
  $png = Join-Path $OutDir "sim_smoke_agg.png"
  Write-Host ">> Headless (Agg) -> $png"
  $args = @(
    "-m","colink_core.sim.run_sweep",
    "--steps","25",
    "--plot",$png,
    "--display","Agg","--no-show"
  )
  $p = & python @args
  if ($LASTEXITCODE -ne 0) { throw "Headless Agg subprocess failed: $p" }
  if (-not (Test-Path $png)) { throw "Expected PNG not found: $png" }
  Write-Host "OK: Agg"
  $script:results += "headless-agg: PASS (wrote $(Split-Path $png -Leaf))"
}

# Show Agg offscreen (we still render to file; don't block)
function Run-ShowAggOffscreen {
  $png = Join-Path $OutDir "sim_smoke_agg.png"
  Write-Host ">> Show Agg (offscreen)"
  $args = @(
    "-m","colink_core.sim.run_sweep",
    "--steps","15",
    "--plot",$png,
    "--display","Agg","--no-show"
  )
  $p = & python @args
  if ($LASTEXITCODE -ne 0) { throw "Show Agg offscreen subprocess failed: $p" }
  Write-Host "OK: Agg"
  $script:results += "show-agg-offscreen: PASS"
}

function Run-ShowHoldTkAgg {
  # Not available headless; mark SKIP unless a GUI is wired up later
  $script:results += "show-hold-tkagg: SKIP (use -IncludeInteractive path if added)"
}

# ---- engine runner: timeseries + slippage + spread (or metrics-only) ----
function Run-SimEngine {
  Write-Host ">> Sim Engine (Agg) for Pairs: $($pairList -join ', ')"
  foreach ($pair in $pairList) {
    $sfx = Pair-Suffix $pair
    $json = Join-Path $OutDir "sim_from_engine_${sfx}.json"
    $png  = Join-Path $OutDir "sim_from_engine_${sfx}.png"
    $slp  = Join-Path $OutDir "sim_from_engine_slippage_${sfx}.png"
    $spr  = Join-Path $OutDir "sim_from_engine_spread_${sfx}.png"

    $args = @(
      "-m","colink_core.sim.run_sweep",
      "--pairs",$pair,
      "--steps","50",
      "--seed","$Seed",
      "--out",$json,
      "--display","Agg","--no-show"
    )

    if (-not $MetricsOnly) {
      $args += @("--plot",$png,"--slippage",$slp,"--spread",$spr)
    } else {
      $args += @("--metrics-only")
    }

    & python @args
    if ($LASTEXITCODE -ne 0) { throw "Sim engine exited with code $LASTEXITCODE (pair=$pair)" }

    if ($MetricsOnly) {
      if (-not (Test-Path $json)) { throw "Expected JSON not found: $json" }
    } else {
      foreach ($f in @($png,$json,$slp,$spr)) {
        if (-not (Test-Path $f)) { throw "Expected output not found: $f" }
      }
    }
  }
  $script:results += ("sim-engine: PASS (pairs=" + ($pairList -join ", ") + ")")
}

# ---- run selection ----
$script:results = @()
switch ($Which) {
  "headless-agg"       { if ($RunSim) { Run-SimEngine }; Run-HeadlessAgg }
  "show-agg-offscreen" { if ($RunSim) { Run-SimEngine }; Run-ShowAggOffscreen }
  "show-hold-tkagg"    { if ($RunSim) { Run-SimEngine }; Run-ShowHoldTkAgg }
  "all"                { if ($RunSim) { Run-SimEngine }; Run-HeadlessAgg; Run-ShowAggOffscreen; Run-ShowHoldTkAgg }
}

# ---- summary ----
Write-Host ""
Write-Host "=== SIM DISPLAY SMOKE SUMMARY ==="
$script:results | ForEach-Object { Write-Host "* $_" }
Write-Host "================================="


