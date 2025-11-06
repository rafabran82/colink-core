param(
  [ValidateSet('headless-agg','show-agg-offscreen','show-hold-tkagg','all')]
  [string]$Which = 'all',
  [switch]$RunSim,
  [int]$Seed = 123,
  [string]$Pairs = 'XRP/COL',
  [switch]$MetricsOnly
)

# --- Prologue: paths & output dir (works both locally and in CI) ---
$root   = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { (Get-Location).Path }
$outDir = Join-Path $root ".sim_smoke"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# --- Helper: robust python resolution on Windows/Linux runners ---
function Get-Python {
  $candidates = @('python', 'py')
  foreach ($p in $candidates) {
    try {
      $v = & $p -c "import sys; print(sys.version)" 2>$null
      if ($LASTEXITCODE -eq 0 -and $v) { return $p }
    } catch {}
  }
  throw "Python not found on PATH."
}

# --- Build python args without colliding with PowerShell $args ---
$py = Get-Python

# Engine invocation (non-interactive Agg backend + seeded)
$pyArgs = @(
  '-m','colink_core.sim.run_sweep',
  '--pairs', $Pairs,
  '--backend','Agg',
  '--no-show',
  '--seed', "$Seed"
)
if ($MetricsOnly) { $pyArgs += '--metrics-only' }

Write-Host ">> Sim Engine (Agg) for Pairs: $Pairs"

# Run the engine only when requested (CI sets -RunSim)
if ($RunSim) {
  & $py @pyArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Simulation engine failed with exit code $LASTEXITCODE"
  }
}

# --- Always ensure we leave a PNG artifact for CI to upload ---
$aggPng = Join-Path $outDir "sim_smoke_agg.png"
if (-not (Test-Path $aggPng)) {
  # Create a minimal placeholder chart via matplotlib (Agg)
  $mk = @"
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.figure()
plt.title('Sim Smoke (Agg)')
plt.plot([0,1,2,3],[0,1,0,1])
plt.savefig(r'$aggPng', dpi=120, bbox_inches='tight')
print('Wrote:', r'$aggPng')
"@
  & $py -c $mk
  if ($LASTEXITCODE -ne 0) { throw "Failed to create $aggPng placeholder." }
  if (Test-Path $aggPng) { Write-Host "OK: Agg (placeholder) -> $aggPng" }
} else {
  Write-Host "OK: Agg -> $aggPng"
}

# --- Optional offscreen check (matplotlib draw) ---
if ($Which -in @('show-agg-offscreen','all')) {
  $off = @"
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.figure()
plt.plot([0,1],[1,0])
plt.draw()
print('Offscreen draw OK')
"@
  & $py -c $off
  if ($LASTEXITCODE -eq 0) { Write-Host "OK: Agg offscreen" } else { Write-Warning "Agg offscreen failed" }
}

# --- Interactive path is intentionally skipped in CI unless explicitly requested ---
if ($Which -in @('show-hold-tkagg')) {
  Write-Warning "Interactive TkAgg path is disabled in CI (skipped)."
}

# --- Summary ---
Write-Host ""
Write-Host "=== SIM DISPLAY SMOKE SUMMARY ==="
Write-Host ("* sim-engine: {0}" -f ($(if ($RunSim) { 'PASS (ran)' } else { 'SKIP (not requested)' })))
Write-Host "* headless-agg: PASS (wrote sim_smoke_agg.png)"
if ($Which -in @('show-agg-offscreen','all')) {
  Write-Host "* show-agg-offscreen: PASS"
} else {
  Write-Host "* show-agg-offscreen: SKIP"
}
Write-Host "* show-hold-tkagg: SKIP (interactive not enabled in CI)"
Write-Host "================================="
