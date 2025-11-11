# scripts/ci.local.ps1
# Local CI: run pytest, emit JSON summary, append NDJSON metrics, optional plot,
# HTML index (with Top-10 slowest tests), bundle zip, and an optional slow gate.

[CmdletBinding()]
param(
  [string]$Python = "python",
  [string]$Out = ".artifacts",
  [switch]$NoTests,
  [switch]$NoPlot,
  [double]$FailIfSlowSec = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ----- Layout
$ciDir       = Join-Path $Out "ci"
$logsDir     = Join-Path $ciDir "logs"
$plotsDir    = Join-Path $Out "plots"
$metricsDir  = Join-Path $Out "metrics"
$bundlesDir  = Join-Path $Out "bundles"

$summaryJson = Join-Path $ciDir "ci_summary.json"
$pytestLog   = Join-Path $ciDir "pytest.txt"
$junitXml    = Join-Path $ciDir "junit.xml"
$ndjsonPath  = Join-Path $metricsDir "run.ndjson"
$plotPath    = Join-Path $plotsDir "summary.png"
$indexHtml   = Join-Path $Out "index.html"

# ----- Ensure directories
$null = New-Item -ItemType Directory -Force -Path $Out,$ciDir,$logsDir,$plotsDir,$metricsDir,$bundlesDir

# ----- Run pytest (portable capture)
$pytestExit  = 0
$durationSec = 0.0
$sw = [Diagnostics.Stopwatch]::StartNew()
if (-not $NoTests) {
  Write-Host "Running tests with $Python -m pytest -rA --durations=0 --junitxml $junitXml ..."
  $out = & $Python -m pytest -rA --durations=0 --junitxml $junitXml 2>&1
  $pytestExit = $LASTEXITCODE
  Set-Content -Path $pytestLog -Value ($out -join [Environment]::NewLine) -Encoding utf8
} else {
  Write-Host "Skipping tests (--NoTests)."
}
$sw.Stop()
$durationSec = [Math]::Round($sw.Elapsed.TotalSeconds,2)

# ----- Parse reports (XML first; text fallback) via Python helper
$pyParse = @"
import sys, re, json, pathlib, datetime, xml.etree.ElementTree as ET
log_path   = pathlib.Path(sys.argv[1])
out_json   = pathlib.Path(sys.argv[2])
ndjson     = pathlib.Path(sys.argv[3])
exitcode   = int(sys.argv[4])
junit_path = pathlib.Path(sys.argv[5])

counts = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
tot = None
dur_total = None
durations = []

def parse_from_junit(p: pathlib.Path):
    global counts, tot, dur_total, durations
    if not p.exists():
        return False
    try:
        tree = ET.parse(str(p))
        root = tree.getroot()
        suites = root.findall('.//testsuite') or [root]
        tests = failures = errors = skipped = 0
        total_time = 0.0
        for s in suites:
            tests    += int(s.attrib.get('tests', 0))
            failures += int(s.attrib.get('failures', 0))
            errors   += int(s.attrib.get('errors', 0))
            skipped  += int(s.attrib.get('skipped', 0))
            try:
                total_time += float(s.attrib.get('time', 0) or 0)
            except Exception:
                pass
            for tc in s.findall('.//testcase'):
                name = (tc.attrib.get('classname','') + '::' + tc.attrib.get('name','')).strip(':')
                try:
                    t = float(tc.attrib.get('time', 0) or 0)
                except Exception:
                    t = None
                durations.append({'name': name, 'seconds': t})
        counts = {
            'passed': max(tests - failures - errors - skipped, 0),
            'failed': failures + errors,
            'skipped': skipped,
            'errors': errors
        }
        tot = tests
        dur_total = total_time if total_time > 0 else None
        return True
    except Exception:
        return False

def parse_from_text(p: pathlib.Path):
    global counts, tot, dur_total
    text = p.read_text(encoding='utf-8') if p.exists() else ''
    m = re.search(r'=+\\s*(.+?)\\s+in\\s+([0-9]*\\.?[0-9]+)s\\s*=+', text)
    if not m:
        return False
    parts = m.group(1).split(',')
    c = {}
    T = 0
    for part in parts:
        part = part.strip()
        mm = re.match(r'(\\d+)\\s+(\\w+)', part)
        if mm:
            n, label = int(mm.group(1)), mm.group(2).lower()
            c[label] = c.get(label, 0) + n
            T += n
    counts['passed']  = c.get('passed', 0)
    counts['failed']  = c.get('failed', 0) + c.get('errors', 0) + c.get('error', 0)
    counts['skipped'] = c.get('skipped', 0) + c.get('xfailed', 0) + c.get('xpassed', 0)
    tot = T or None
    try:
        dur_total = float(m.group(2))
    except Exception:
        dur_total = None
    return True

ok = parse_from_junit(junit_path) or parse_from_text(log_path)

result = {
    'exit_code': exitcode,
    'tests_total': tot,
    'passed': counts.get('passed',0),
    'failed': counts.get('failed',0),
    'skipped': counts.get('skipped',0),
    'time_total_sec': dur_total,
    'durations': [d for d in durations if d.get('seconds') is not None][:200]
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
nd = {
    'ts': ts,
    'exit': exitcode,
    'tests_total': result['tests_total'],
    'passed': result['passed'],
    'failed': result['failed'],
    'skipped': result['skipped'],
    'time_total_sec': result['time_total_sec']
}
ndjson.parent.mkdir(parents=True, exist_ok=True)
with ndjson.open('a', encoding='utf-8') as f:
    f.write(json.dumps(nd, ensure_ascii=False) + '\\n')
"@
$tmpPy = Join-Path $env:TEMP ("ci_parse_{0}.py" -f ([guid]::NewGuid()))
Set-Content -Path $tmpPy -Value $pyParse -Encoding utf8
try {
  & $Python $tmpPy $pytestLog $summaryJson $ndjsonPath $pytestExit $junitXml | Out-Null
} finally {
  Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
}

# ----- Load summary and compute slow table + gate (ALWAYS define $finalExit)
$sum = ConvertFrom-Json (Get-Content -Raw $summaryJson)
if ($null -eq $sum) {
  $sum = [pscustomobject]@{
    exit_code      = $pytestExit
    tests_total    = $null
    passed         = $null
    failed         = $null
    skipped        = $null
    time_total_sec = $null
    durations      = @()
  }
}

$slowRows = ""
$top = @($sum.durations | Where-Object { $_.seconds -ne $null } | Sort-Object seconds -Descending | Select-Object -First 10)
foreach ($d in $top) {
  $n = ($d.name -replace '<','&lt;' -replace '>','&gt;')
  $s = "{0:N3}" -f [double]$d.seconds
  $slowRows += "<tr><td><code>$n</code></td><td style='text-align:right'>$s</td></tr>`n"
}
if (-not $slowRows) { $slowRows = "<tr><td colspan='2'><em>No timing data available.</em></td></tr>" }

$maxSeconds = ($top | Select-Object -ExpandProperty seconds | Measure-Object -Maximum).Maximum
if (-not $maxSeconds) { $maxSeconds = 0 }
$gateViolated = ($FailIfSlowSec -gt 0 -and [double]$maxSeconds -ge $FailIfSlowSec)
$finalExit = if ($gateViolated) { 2 } else { [int]$sum.exit_code }

# ----- Optional plot (simple pass/fail bar)
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
    & $Python $tmpPy2 $summaryJson $plotPath | Out-Null
  } catch {
    Write-Warning "Plot generation failed (matplotlib not available?). Continuing."
  } finally {
    Remove-Item $tmpPy2 -Force -ErrorAction SilentlyContinue
  }
}

# ----- index.html
$passFail = if ($finalExit -eq 0) { "PASS" } else { "FAIL" }
$gateNote = if ($FailIfSlowSec -gt 0) { "(gate: ≥ $FailIfSlowSec s ⇒ exit 2)" } else { "" }
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
  .grid{display:grid;grid-template-columns:1fr;gap:1rem;max-width:960px}
  img{max-width:560px;border:1px solid #ddd;border-radius:8px}
  table{border-collapse:collapse}
  th,td{padding:.35rem .6rem;border:1px solid #eee}
  th{background:#fafafa;text-align:left}
  td:last-child{white-space:nowrap}
</style>
<body>
  <h1>Local CI Summary</h1>
  <div>Status: <span class="chip ${passFail=='PASS' ? 'ok' : 'bad'}">$passFail</span> <small>$gateNote</small></div>
  <div class="grid">
    <div><strong>pytest exit:</strong> <code>$($sum.exit_code)</code></div>
    <div><strong>final exit:</strong> <code>$finalExit</code></div>
    <div><strong>duration (wall):</strong> <code>$durationSec s</code></div>
    <div><strong>generated:</strong> <code>$((Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ssZ"))</code></div>
    <div>
      <a href="ci/ci_summary.json">ci/ci_summary.json</a> •
      <a href="ci/pytest.txt">ci/pytest.txt</a> •
      <a href="ci/junit.xml">ci/junit.xml</a> •
      <a href="metrics/run.ndjson">metrics/run.ndjson</a>
    </div>
    <div><em>summary plot (if generated)</em><br/><img src="plots/summary.png" alt="summary plot"/></div>
  </div>

  <h3>Counts</h3>
  <table>
    <tr><th>total</th><th>passed</th><th>failed</th><th>skipped</th><th>time_total_sec</th></tr>
    <tr><td>$($sum.tests_total)</td><td>$($sum.passed)</td><td>$($sum.failed)</td><td>$($sum.skipped)</td><td>$($sum.time_total_sec)</td></tr>
  </table>

  <h3>Top 10 slowest tests</h3>
  <table>
    <tr><th>test</th><th>seconds</th></tr>
    $slowRows
  </table>

  <p><small>Max observed test time this run: <code>{0:N3}s</code>.</small></p>
</body>
</html>
"@ -f ([double]$maxSeconds)

Set-Content -Path $indexHtml -Value $html -Encoding utf8

# ----- Bundle snapshot (zip)
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$bundle = Join-Path $bundlesDir ("run-{0}.zip" -f $stamp)
$bundleInputs = @()
$bundleInputs += $summaryJson
if (Test-Path $pytestLog) { $bundleInputs += $pytestLog }
if (Test-Path $junitXml)  { $bundleInputs += $junitXml }
if (Test-Path $plotPath)  { $bundleInputs += $plotPath }
if (Test-Path $indexHtml) { $bundleInputs += $indexHtml }
if (Test-Path $ndjsonPath){ $bundleInputs += $ndjsonPath }
if (Test-Path $bundle) { Remove-Item $bundle -Force }
if ($bundleInputs.Count -gt 0) {
  Compress-Archive -Path $bundleInputs -DestinationPath $bundle -Force
  Write-Host "Bundle created: $bundle"
}

Write-Host "Local CI completed. Summary: $summaryJson"
Write-Host "Index: $indexHtml"
if (Test-Path $plotPath) { Write-Host "Plot: $plotPath" }

exit $finalExit
