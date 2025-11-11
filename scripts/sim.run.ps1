$ErrorActionPreference = "Stop"

# --- Sim Run Stub (Phase 3, Step 1) ---
$repo   = (git rev-parse --show-toplevel)
Set-Location $repo

$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $repo ".artifacts\data\$stamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host "🧩 Sim run started: $stamp"
Write-Host "📂 Output folder: $outDir"

# For now, just write a tiny meta JSON
$meta = @{
    run_id     = $stamp
    created_at = (Get-Date).ToString("s")
    note       = "Phase3-Step1 stub run"
}
$meta | ConvertTo-Json | Set-Content (Join-Path $outDir "run_meta.json") -Encoding utf8

Write-Host "✅ Created run_meta.json"
Write-Host "✅ Dashboard refreshed (simulated) at .artifacts\index.html"
# --- CALL PYTHON STUB (Step 2) ---
# Resolve python exe robustly (PS 5.1-safe)
$cmd = Get-Command python -ErrorAction SilentlyContinue
$pyExe = if ($cmd) { $cmd.Path } else { "python" }

Write-Host "🐍 Running Python sim stub ..."
& $pyExe "scripts/sim.run.py" --out $outDir --n 60 --dt 0.01
if ($LASTEXITCODE -ne 0) { throw "Python sim stub failed ($LASTEXITCODE)" }

# List produced files
Write-Host "   - " (Join-Path $outDir "events.ndjson")
Write-Host "   - " (Join-Path $outDir "metrics.json")

# (Optional next step) Refresh dashboard when ready
# .\rebuild_ci.cmd
# --- APPEND SUMMARY CSV (Step 3) ---
$metricsPath = Join-Path $outDir "metrics.json"
$summaryCsv  = Join-Path $repo ".artifacts\metrics\summary.csv"

# Ensure metrics folder
$summaryDir = Split-Path -Parent $summaryCsv
New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null

if (-not (Test-Path -LiteralPath $metricsPath)) {
    throw "Expected metrics.json not found: $metricsPath"
}

$m = Get-Content -Raw -LiteralPath $metricsPath | ConvertFrom-Json
# Values we’ll track across runs (minimal set for now)
$ts     = (Get-Date).ToUniversalTime().ToString("s")
$samples= [int]$m.samples
$avg    = [double]$m.total_mb_avg
$p95    = [double]$m.total_mb_p95
$max    = [double]$m.total_mb_max

# Write header if file missing
if (-not (Test-Path -LiteralPath $summaryCsv)) {
    "timestamp_utc,samples,total_mb_avg,total_mb_p95,total_mb_max" | Set-Content -LiteralPath $summaryCsv -Encoding utf8
}

# Append row
"$ts,$samples,$avg,$p95,$max" | Add-Content -LiteralPath $summaryCsv -Encoding utf8

Write-Host "🧮 Appended summary:" -ForegroundColor Green
Write-Host "   $summaryCsv"
# --- PLOT SUMMARY (Step 4) ---
$summaryCsv = Join-Path $repo ".artifacts\metrics\summary.csv"
$summaryPng = Join-Path $repo ".artifacts\metrics\summary.png"

$cmd = Get-Command python -ErrorAction SilentlyContinue
$pyExe = if ($cmd) { $cmd.Path } else { "python" }

& $pyExe "scripts/sim.plot.py" --csv "$summaryCsv" --out "$summaryPng"
if ($LASTEXITCODE -ne 0) { Write-Warning "summary plot failed ($LASTEXITCODE)" } else {
  Write-Host "🖼  Summary plot:" $summaryPng
}
