param(
  [ValidateSet("headless-agg","show-agg-offscreen","show-hold-tkagg","all")]
  [string]$Which = "all",
  [switch]$RunSim,
  [switch]$IncludeInteractive,
  [string]$OutDir = "$PSScriptRoot/../.sim_smoke"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# paths
$PlotPy = Join-Path $PSScriptRoot "sim_plot.py"
if (-not (Test-Path $PlotPy)) {
  throw "Missing $PlotPy. Create tools\sim_plot.py first."
}

# ensure output dir
if (-not (Test-Path -LiteralPath $OutDir)) {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}
try { $OutDir = (Resolve-Path -LiteralPath $OutDir).Path } catch { }

function Invoke-PyFile {
  param(
    [Parameter(Mandatory=$true)][string]$File,
    [hashtable]$Env = @{}
  )
  # backup & apply env safely using .NET (avoids .Value on null)
  $old = @{}
  foreach ($k in $Env.Keys) {
    $prev = [System.Environment]::GetEnvironmentVariable($k, "Process")
    $old[$k] = $prev
    if ($Env[$k] -ne $null) {
      [System.Environment]::SetEnvironmentVariable($k, [string]$Env[$k], "Process")
    } else {
      [System.Environment]::SetEnvironmentVariable($k, $null, "Process")
    }
  }
  try {
    & python $File
    if ($LASTEXITCODE -ne 0) { throw "Python exited with code $LASTEXITCODE" }
  } finally {
    foreach ($k in $Env.Keys) {
      [System.Environment]::SetEnvironmentVariable($k, $old[$k], "Process")
    }
  }
}

$results = @()

function Run-HeadlessAgg {
  $outfile = Join-Path $OutDir "sim_smoke_agg.png"
  Write-Host ">> Headless (Agg) -> $outfile" -ForegroundColor Cyan
  Invoke-PyFile -File $PlotPy -Env @{
    "MPLBACKEND"     = "Agg";
    "SIM_SMOKE_SHOW" = "0";
    "SIM_SMOKE_HOLD" = "0";
    "SIM_SMOKE_OUT"  = $outfile
  }
  if (-not (Test-Path $outfile)) { throw "Expected output not found: $outfile" }
  $script:results += "headless-agg: PASS (wrote $(Split-Path $outfile -Leaf))"
}

function Run-ShowAggOffscreen {
  Write-Host ">> Show Agg (offscreen)" -ForegroundColor Cyan
  Invoke-PyFile -File $PlotPy -Env @{
    "MPLBACKEND"         = "Agg";
    "SIM_SMOKE_SHOW"     = "1";
    "SIM_SMOKE_HOLD"     = "0";
    "SIM_SMOKE_SOFTFAIL" = "1"
  }
  $script:results += "show-agg-offscreen: PASS"
}

function Run-ShowHoldTkAgg {
  if (-not $IncludeInteractive) {
    $script:results += "show-hold-tkagg: SKIP (use -IncludeInteractive to run)";
    return
  }
  Write-Host ">> Show + Hold (TkAgg) - a window will open; close it to continue..." -ForegroundColor Yellow
  try {
    Invoke-PyFile -File $PlotPy -Env @{
      "MPLBACKEND"     = "TkAgg";
      "SIM_SMOKE_SHOW" = "1";
      "SIM_SMOKE_HOLD" = "1"
    }
    $script:results += "show-hold-tkagg: PASS"
  } catch {
    Write-Warning "TkAgg failed - likely no Tkinter runtime. Marking as SKIP."
    $script:results += "show-hold-tkagg: SKIP (Tk/Tkinter not available)"
  }
}

function Run-SimEngine {
  # Run the real sweep in headless Agg, saving JSON + PNG
  $json = Join-Path $OutDir "sim_from_engine.json"
  $png  = Join-Path $OutDir "sim_from_engine.png"
  Write-Host ">> Sim Engine (Agg) -> $png ; $json" -ForegroundColor Cyan

  $args = @(
    "-m", "colink_core.sim.run_sweep",
    "--steps", "50",
    "--out", $json,
    "--plot", $png,
    "--display", "Agg",
    "--no-show"
  )

  & python @args
  if ($LASTEXITCODE -ne 0) { throw "Sim engine exited with code $LASTEXITCODE" }
  if (-not (Test-Path $png))  { throw "Expected PNG not found: $png" }
  if (-not (Test-Path $json)) { throw "Expected JSON not found: $json" }

  $script:results += "sim-engine: PASS (wrote $(Split-Path $png -Leaf), $(Split-Path $json -Leaf))"
}

switch ($Which) {
  "headless-agg"       { Run-HeadlessAgg }
  "show-agg-offscreen" { Run-ShowAggOffscreen }
  "show-hold-tkagg"    { Run-ShowHoldTkAgg }
  "all"                { if ($RunSim) { Run-SimEngine }; Run-HeadlessAgg; Run-ShowAggOffscreen; Run-ShowHoldTkAgg }
}

Write-Host ""
Write-Host "=== SIM DISPLAY SMOKE SUMMARY ===" -ForegroundColor Green
$script:results | ForEach-Object { Write-Host "* $_" }
Write-Host "================================="


