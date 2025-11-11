# scripts/ci.local.ps1
# Local CI: tests -> JSON summary + NDJSON metrics + plot + index + zip bundle
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

# --- Layout
$ciDir      = Join-Path $Out "ci"
$logsDir    = Join-Path $ciDir "logs"
$plotsDir   = Join-Path $Out "plots"
$metricsDir = Join-Path $Out "metrics"
$bundlesDir = Join-Path $Out "bundles"

$summaryJsonPath = Join-Path $ciDir "ci_summary.json"
$pytestLogPath   = Join-Path $ciDir "pytest.txt"
$ndjsonPath      = Join-Path $metricsDir "run.ndjson"
$plotPath        = Join-Path $plotsDir "summary.png"
$indexHtml       = Join-Path $Out "index.html"

# --- Ensure directories
$null = New-Item -ItemType Directory -Force -Path $Out,$ciDir,$logsDir,$plotsDir,$metricsDir,$bundlesDir

# --- Run pytest (portable capture)
$pytestExit  = 0
$durationSec = 0.0
$sw = [Diagnostics.Stopwatch]::StartNew()
if (-not $NoTests) {
  Write-Host "Running tests with $Python -m pytest -rA --durations=0 ..."
  # Capture stdout+stderr in-process (works on Windows PowerShell + pwsh)
  $out = & $Python -m pytest -rA --durations=0 2>&1
  $pytestExit = $LASTEXITCODE
  Set-Content -Path $pytestLogPath -Value ($out -join [Environment]::NewLine) -Encoding utf8
} else {
  Write-Host "Skipping tests (--NoTests)."
}
$sw.Stop()
$durationSec = [Math]::Round($sw.Elapsed.TotalSeconds,2)

# --- Parse pytest log with a small Python helper (robust)
$pyParse = @"
import sys, re, json, pathlib, datetime
log_path = pathlib.Path(sys.argv[1])
out_json = pathlib.Path(sys.argv[2])
ndjson   = pathlib.Path(sys.argv[3])
exitcode = int(sys.argv[4])
text = log_path.read_text(encoding='utf-8') if log_path.exists() else ''

m = re.search(r"=+\s*(.+?)\s+in\s+([0-9]*\.?[0-9]+)s\s*=+", text)
counts = {}
tot = 0
dur_total = None
if m:
    parts = m.group(1).split(",")
    for part in parts:
        part = part.strip()
        mm = re.match(r"(\d+)\s+(\w+)", part)
        if mm:
            n, label = int(mm.group(1)), mm.group(2).lower()
            counts[label] = counts.get(label, 0) + n
            tot += n
    try:
        dur_total = float(m.group(2))
    except Exception:
        dur_total = None

durations = []
for sec, name in re.findall(r"^\s*([0-9]*\.?[0-9]+)s\s+\w+\s+(.+)$", text, flags=re.M):
    try:
        durations.append({"name": name.strip(), "seconds": float(sec)})
    except Exception:
        pass

passed  = counts.get("passed", 0)
failed  = counts.get("failed", 0) + counts.get("errors", 0) + counts.get("error", 0)
skipped = counts.get("skipped", 0) + counts.get("xfailed", 0) + counts.get("xpassed", 0)

result = {
    "exit_code": exitcode,
    "tests_total": tot or None,
    "passed": passed,
    "failed": failed,
    "skipped": skipped,
    "time_total_sec": dur_total,
    "durations": durations[:200]
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

nd = {
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z"),
    "exit": exitcode,
    "tests_total": result["tests_total"],
    "passed": passed,
    "failed": failed,
    "skipped": skipped,
    "time_total_sec": result["time_total_sec"]
}
ndjson.parent.mkdir(parents=True, exist_ok=True)
with ndjson.open("a", encoding="utf-8") as f:
    f.write(json.dumps(nd, ensure_ascii=False) + "\n")
"@
$tmpPy = Join-Path $env:TEMP ("ci_parse_{0}.py" -f ([guid]::NewGuid()))
Set-Content -Path $tmpPy -Value $pyParse -Encoding utf8
try {
  & $Python $tmpPy $pytestLogPath $summaryJsonPath $ndjsonPath $pytestExit | Out-Null
} finally {
  Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
}

# --- Plot (optional; pass=1 fail=0)
if (-not $NoPlot) {
  $py = @"
import json, sys, pathlib
from matplotlib import pyplot as plt
summary = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
value = 1 if int(summary.get('exit_code', 1)) == 0 else 0
plt.figure()
plt.bar(['tests'], [value])
plt.title(f"Local CI: pass={1 if value==1 else 0}, fail={0 if value==1 else 1}")
out = pathlib.Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out)
"@
  $tmpPy2 = Join-Path $env:TEMP ("ci_plot_{0}.py" -f ([guid]::NewGuid()))
  Set-Content -Path $tmpPy2 -Value $py -Encoding utf8
  try {
    & $Python $tmpPy2 $summaryJsonPath $plotPath | Out-Null
  } catch {
    Write-Warning "Plot generation failed (matplotlib not available?). Continuing."
  } finally {
    Remove-Item $tmpPy2 -Force -ErrorAction SilentlyContinue
  }
}

# --- index.html
$sum = ConvertFrom-Json (Get-Content -Raw $summaryJsonPath)
$passFail = if ($sum.exit_code -eq 0) { "PASS" } else { "FAIL" }
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
  .grid{display:grid;grid-template-columns:1fr;gap:1rem;max-width:880px}
  img{max-width:560px;border:1px solid #ddd;border-radius:8px}
  table{border-collapse:collapse}
  th,td{padding:.25rem .5rem;border:1px solid #eee}
</style>
<body>
  <h1>Local CI Summary</h1>
  <div>Status: <span class="chip ${passFail=='PASS' ? 'ok' : 'bad'}">$passFail</span></div>
  <div class="grid">
    <div><strong>pytest exit:</strong> <code>$($sum.exit_code)</code></div>
    <div><strong>duration:</strong> <code>$durationSec s</code></div>
    <div><strong>generated:</strong> <code>$((Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ssZ"))</code></div>
    <div><a href="ci/ci_summary.json">ci/ci_summary.json</a> • <a href="ci/pytest.txt">ci/pytest.txt</a> • <a href="metrics/run.ndjson">metrics/run.ndjson</a></div>
    <div><em>summary plot (if generated)</em><br/><img src="plots/summary.png" alt="summary plot"/></div>
  </div>
  <h3>Counts</h3>
  <table>
    <tr><th>total</th><th>passed</th><th>failed</th><th>skipped</th><th>time_total_sec</th></tr>
    <tr><td>$($sum.tests_total)</td><td>$($sum.passed)</td><td>$($sum.failed)</td><td>$($sum.skipped)</td><td>$($sum.time_total_sec)</td></tr>
  </table>
</body>
</html>
"@
Set-Content -Path $indexHtml -Value $html -Encoding utf8

# --- Bundle snapshot (zip)
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$bundle = Join-Path $bundlesDir ("run-{0}.zip" -f $stamp)

$bundleInputs = @()
$bundleInputs += $summaryJsonPath
if (Test-Path $pytestLogPath) { $bundleInputs += $pytestLogPath }
if (Test-Path $plotPath)      { $bundleInputs += $plotPath }
if (Test-Path $indexHtml)     { $bundleInputs += $indexHtml }
if (Test-Path $ndjsonPath)    { $bundleInputs += $ndjsonPath }

if (Test-Path $bundle) { Remove-Item $bundle -Force }
if ($bundleInputs.Count -gt 0) {
  Compress-Archive -Path $bundleInputs -DestinationPath $bundle -Force
  Write-Host "Bundle created: $bundle"
}

Write-Host "Local CI completed. Summary: $summaryJsonPath"
Write-Host "Index: $indexHtml"
if (Test-Path $plotPath) { Write-Host "Plot: $plotPath" }
exit $sum.exit_code

