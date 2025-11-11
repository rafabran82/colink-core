# scripts/ci.local.ps1
# Local CI: run tests, emit JSON summary + plot + index.html under .artifacts/
# Usage: pwsh -NoProfile -File scripts/ci.local.ps1 [-Python python] [-Out .artifacts] [-NoTests] [-NoPlot]

[CmdletBinding()]
param(
  [string]$Python = "python",
  [string]$Out = ".artifacts",
  [switch]$NoTests,
  [switch]$NoPlot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- 0) Layout
$ciDir     = Join-Path $Out "ci"
$plotsDir  = Join-Path $Out "plots"
$metricsDir= Join-Path $Out "metrics"
$dataDir   = Join-Path $Out "data"
$bundlesDir= Join-Path $Out "bundles"
$summary   = Join-Path $ciDir "ci_summary.json"
$plotPath  = Join-Path $plotsDir "summary.png"
$indexHtml = Join-Path $Out "index.html"

# --- 1) Ensure directories
$null = New-Item -ItemType Directory -Force -Path $Out,$ciDir,$plotsDir,$metricsDir,$dataDir,$bundlesDir

# --- 2) Run pytest (optional)
$pytestExit = 0
$durationSec = 0.0
$sw = [Diagnostics.Stopwatch]::StartNew()
if (-not $NoTests) {
  Write-Host "Running tests with $Python -m pytest -q ..."
  & $Python -m pytest -q
  $pytestExit = $LASTEXITCODE
} else {
  Write-Host "Skipping tests (--NoTests)."
}
$sw.Stop()
$durationSec = [Math]::Round($sw.Elapsed.TotalSeconds,2)

# --- 3) Write JSON summary
$summaryObj = [ordered]@{
  timestamp_iso   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
  python          = $Python
  pytest_exit     = $pytestExit
  duration_sec    = $durationSec
  cwd             = (Get-Location).Path
  notes           = "Local CI summary. 0 = tests passed; non-zero = failures or errors."
}
$summaryJson = $summaryObj | ConvertTo-Json -Depth 5
Set-Content -Path $summary -Value $summaryJson -Encoding utf8

# --- 4) Plot (optional, requires matplotlib)
if (-not $NoPlot) {
  $py = @"
import json, sys, pathlib, matplotlib
from matplotlib import pyplot as plt

summary = json.load(open(sys.argv[1], "r", encoding="utf-8"))
# Simple bar: 1=pass, 0=fail
value = 1 if int(summary.get("pytest_exit", 1)) == 0 else 0
plt.figure()
plt.bar(["tests"], [value])
plt.title("Local CI: pass=1, fail=0")
out = pathlib.Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out)
"@
  $tmpPy = Join-Path $env:TEMP ("ci_plot_{0}.py" -f ([guid]::NewGuid()))
  Set-Content -Path $tmpPy -Value $py -Encoding utf8
  try {
    & $Python $tmpPy $summary $plotPath | Out-Null
  } catch {
    Write-Warning "Plot generation failed (matplotlib not available?). Continuing."
  } finally {
    Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
  }
} else {
  Write-Host "Skipping plot (--NoPlot)."
}

# --- 5) index.html
$passFail = if ($pytestExit -eq 0) { "PASS" } else { "FAIL" }
$html = @"
<!doctype html>
<html lang="en">
<meta charset="utf-8"/>
<title>Local CI Summary</title>
<style>
  body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:2rem;line-height:1.5}
  .chip{display:inline-block;padding:.25rem .6rem;border-radius:9999px;font-weight:600}
  .ok{background:#e6ffed;border:1px solid #b7ebc6;color:#096c38}
  .bad{background:#ffecec;border:1px solid #ffb3b3;color:#8a1f11}
  code{background:#f5f5f5;padding:.15rem .35rem;border-radius:.25rem}
  .grid{display:grid;grid-template-columns:1fr;gap:1rem;max-width:820px}
  img{max-width:560px;border:1px solid #ddd;border-radius:8px}
</style>
<body>
  <h1>Local CI Summary</h1>
  <div>Status: <span class="chip ${passFail=='PASS' ? 'ok' : 'bad'}">$passFail</span></div>
  <div class="grid">
    <div><strong>pytest exit:</strong> <code>$pytestExit</code></div>
    <div><strong>duration:</strong> <code>$durationSec s</code></div>
    <div><strong>generated:</strong> <code>$((Get-Date).ToString("u"))</code></div>
    <div><a href="ci/ci_summary.json">ci/ci_summary.json</a></div>
    <div>
      <div><em>summary plot (if generated)</em></div>
      <img src="plots/summary.png" alt="summary plot"/>
    </div>
  </div>
</body>
</html>
"@
Set-Content -Path $indexHtml -Value $html -Encoding utf8

Write-Host "Local CI completed. Summary: $summary"
Write-Host "Index: $indexHtml"
if (Test-Path $plotPath) { Write-Host "Plot: $plotPath" }
exit $pytestExit
