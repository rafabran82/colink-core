param(
  [ValidateSet("headless-agg","show-agg-offscreen","show-hold-tkagg","all")]
  [string]$Which = "all",
  [switch]$RunSim,
  [string]$Pairs = "XRP/COL",
  [switch]$IncludeInteractive,
  [string]$OutDir = "$PSScriptRoot/../.sim_smoke"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $OutDir)) {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}
try { $OutDir = (Resolve-Path -LiteralPath $OutDir).Path } catch { }

$PlotPy = Join-Path $PSScriptRoot "sim_plot.py"
if (-not (Test-Path $PlotPy)) {
  throw "Missing tools\sim_plot.py (expected at $PlotPy)."
}

function Invoke-PyFile {
  param(
    [Parameter(Mandatory=$true)][string]$File,
    [hashtable]$Env = @{}
  )
  $old = @{}
  foreach ($k in $Env.Keys) {
    $cur = Get-Item Env:$k -ErrorAction SilentlyContinue
    $old[$k] = if ($null -ne $cur) { $cur.Value } else { $null }
    if ($Env[$k] -ne $null) { Set-Item Env:$k -Value $Env[$k] }
    else { Remove-Item Env:$k -ErrorAction SilentlyContinue }
  }
  try {
    & python $File
    if ($LASTEXITCODE -ne 0) { throw "Python exited with code $LASTEXITCODE" }
  } finally {
    foreach ($k in $Env.Keys) {
      if ($old.ContainsKey($k) -and $null -ne $old[$k]) { Set-Item Env:$k -Value $old[$k] }
      else { Remove-Item Env:$k -ErrorAction SilentlyContinue }
    }
  }
}

function Slugify([string]$s) { return ($s -replace '[^A-Za-z0-9]+','-').ToLower() }

$script:results = @()

function Run-HeadlessAgg {
  $outfile = Join-Path $OutDir "sim_smoke_agg.png"
  Write-Host ">> Headless (Agg) -> $outfile"
  Invoke-PyFile -File $PlotPy -Env @{
    "MPLBACKEND"     = "Agg"
    "SIM_SMOKE_SHOW" = "0"
    "SIM_SMOKE_HOLD" = "0"
    "SIM_SMOKE_OUT"  = $outfile
  }
  if (-not (Test-Path $outfile)) { throw "Expected output not found: $outfile" }
  $script:results += "headless-agg: PASS (wrote $(Split-Path $outfile -Leaf))"
}

function Run-ShowAggOffscreen {
  Write-Host ">> Show Agg (offscreen)"
  Invoke-PyFile -File $PlotPy -Env @{
    "MPLBACKEND"         = "Agg"
    "SIM_SMOKE_SHOW"     = "1"
    "SIM_SMOKE_HOLD"     = "0"
    "SIM_SMOKE_SOFTFAIL" = "1"
  }
  $script:results += "show-agg-offscreen: PASS"
}

function Run-ShowHoldTkAgg {
  if (-not $IncludeInteractive) {
    $script:results += "show-hold-tkagg: SKIP (use -IncludeInteractive to run)"
    return
  }
  Write-Host ">> Show + Hold (TkAgg) - a window will open; close it to continue..."
  try {
    Invoke-PyFile -File $PlotPy -Env @{
      "MPLBACKEND"     = "TkAgg"
      "SIM_SMOKE_SHOW" = "1"
      "SIM_SMOKE_HOLD" = "1"
    }
    $script:results += "show-hold-tkagg: PASS"
  } catch {
    Write-Warning "TkAgg failed — likely no Tkinter runtime. Marking as SKIP."
    $script:results += "show-hold-tkagg: SKIP (Tk/Tkinter not available)"
  }
}

function Run-SimEngine {
  $pairList = $Pairs -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  Write-Host ">> Sim Engine (Agg) for Pairs: $($pairList -join ', ')"

  foreach ($p in $pairList) {
    $slug = Slugify $p
    $json = Join-Path $OutDir "sim_from_engine_${slug}.json"
    $png  = Join-Path $OutDir "sim_from_engine_${slug}.png"
    $slp  = Join-Path $OutDir "sim_from_engine_slippage_${slug}.png"
    $spr  = Join-Path $OutDir "sim_from_engine_spread_${slug}.png"

    $args = @(
      "-m", "colink_core.sim.run_sweep",
      "--pairs", $p,             # run ONCE per pair
      "--steps", "50", "--seed", "$Seed",
      "--out", $json,
      "--plot", $png,
      "--slippage", $slp,
      "--spread", $spr,
      "--display", "Agg",
      "--no-show"
    )
    & python @args
    if ($LASTEXITCODE -ne 0) { throw "Sim engine exited with code $LASTEXITCODE for pair '$p'" }

    foreach ($f in @($png,$json,$slp,$spr)) {
      if (-not (Test-Path $f)) { throw "Expected output not found: $f" }
    }
  }

  $script:results += "sim-engine: PASS (pairs=$($pairList -join ', '))"
}

if ($RunSim) { Run-SimEngine }

switch ($Which) {
  "headless-agg"       { Run-HeadlessAgg }
  "show-agg-offscreen" { Run-ShowAggOffscreen }
  "show-hold-tkagg"    { Run-ShowHoldTkAgg }
  "all"                { Run-HeadlessAgg; Run-ShowAggOffscreen; Run-ShowHoldTkAgg }
}

Write-Host ""
Write-Host "=== SIM DISPLAY SMOKE SUMMARY ==="
$script:results | ForEach-Object { Write-Host "* $_" }
Write-Host "================================="

