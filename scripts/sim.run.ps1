# --- Python syntax guard (fast fail) ---
. (Join-Path $PSScriptRoot "ci.guard-python.ps1")
Invoke-PythonSyntaxGuard -Root "scripts" -Include @("*.py")
Write-Host "✅ Python lint check passed for all scripts." -ForegroundColor Green
# --- end guard ---
$ErrorActionPreference = "Stop"

function New-Stamp { ([DateTime]::UtcNow).ToString("yyyyMMdd-HHmmss") }

# --- 1) Prepare run folder + meta ---
$stamp  = New-Stamp
$outDir = Join-Path ".artifacts\data" $stamp
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$meta = [ordered]@{
  run_id     = $stamp
  created_at = (Get-Date).ToUniversalTime().ToString("s")
  note       = "Phase3-Step1 stub run"
}
$metaPath = Join-Path $outDir "run_meta.json"
$meta | ConvertTo-Json | Set-Content -LiteralPath $metaPath -Encoding utf8

Write-Host "🧩 Sim run started: $stamp"
Write-Host "📂 Output folder: $((Resolve-Path $outDir).Path)"
Write-Host "✅ Created run_meta.json"

# --- 2) Locate Python ---
$pyExe = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $pyExe) { $pyExe = (Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1).Source }
if (-not $pyExe) { throw "Python executable not found on PATH" }

# --- 3) Run sim stub (writes events.ndjson + metrics.json) ---
& $pyExe "scripts/sim.run.py" --out $outDir --n 60 --dt 0.01
if ($LASTEXITCODE -ne 0) { throw "sim.run.py failed with exit $LASTEXITCODE" }

Write-Host "   -  $(Join-Path $outDir 'events.ndjson')"
Write-Host "   -  $(Join-Path $outDir 'metrics.json')"

# --- 4) Append summary row + plot ---
$metricsPath = Join-Path $outDir "metrics.json"
$summaryDir  = ".artifacts/metrics"
$summaryCsv  = Join-Path $summaryDir "summary.csv"
$summaryPng  = Join-Path $summaryDir "summary.png"
New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null

# ensure header
if (-not (Test-Path $summaryCsv)) {
  "timestamp_utc,samples,total_mb_avg,total_mb_p95,total_mb_max,latency_ms_p95" | Out-File $summaryCsv -Encoding utf8
}

if (Test-Path $metricsPath) {
  $m = Get-Content $metricsPath -Raw | ConvertFrom-Json
  $ts     = $m.generated_at
  $samples= $m.samples
  $avg    = $m.total_mb_avg
  $p95    = $m.total_mb_p95
  $max    = $m.total_mb_max
  $latp95 = $m.latency_ms_p95

  $row = "{0},{1},{2},{3},{4},{5}" -f $ts,$samples,$avg,$p95,$max,$latp95
  $row | Out-File $summaryCsv -Append -Encoding utf8

  Write-Host "🧮 Appended summary:`n   $((Resolve-Path $summaryCsv).Path)"

  # plot summary
  & $pyExe "scripts/sim.plot.py" --csv $summaryCsv --out $summaryPng
  if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Wrote $((Resolve-Path $summaryPng).Path)"
    Write-Host "🖼  Summary plot: $((Resolve-Path $summaryPng).Path)"
  } else {
    Write-Warning "summary plot failed ($LASTEXITCODE)"
  }
} else {
  Write-Warning "metrics.json not found at $metricsPath"
}

# --- 5) Best-effort dashboard refresh ---
try {
  Write-Host "🔄 Refreshing dashboard..."
  if (Test-Path ".\rebuild_ci.cmd") {
    & .\rebuild_ci.cmd
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "rebuild_ci.cmd exited with code $LASTEXITCODE"
    } else {
      Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd."
    }
  } elseif (Test-Path "scripts\ci.rebuild.ps1") {
    pwsh -NoProfile -ExecutionPolicy Bypass -File "scripts\ci.rebuild.ps1"
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "ci.rebuild.ps1 exited with code $LASTEXITCODE"
    } else {
      Write-Host "✅ Dashboard refreshed via scripts\ci.rebuild.ps1."
    }
  } else {
    Write-Warning "No rebuild script found."
  }
} catch {
  Write-Host ("⚠️ Skipped dashboard refresh: " + $_.Exception.Message)
}




