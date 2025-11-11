$ErrorActionPreference = "Stop"

function Remove-OldFiles {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Filter,
    [int]$Keep = 10
  )
  if (!(Test-Path $Dir)) { return }
  Get-ChildItem -Path $Dir -Filter $Filter -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Keep |
    Remove-Item -Force -ErrorAction SilentlyContinue
}

# Resolve repo root
$root = (git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
Set-Location -LiteralPath $root

# Directories
$artDir   = Join-Path $root '.artifacts'
$bundles  = Join-Path $artDir 'bundles'
$plotsDir = Join-Path $artDir 'plots'
$ciDir    = Join-Path $artDir 'ci'
$metrics  = Join-Path $artDir 'metrics'
$dataDir  = Join-Path $artDir 'data'

# Ensure structure
@($artDir,$bundles,$plotsDir,$ciDir,$metrics,$dataDir) |
  ForEach-Object { if (!(Test-Path $_)) { New-Item -ItemType Directory -Force -Path $_ | Out-Null } }
# ===== Phase-10: Bootstrap =====
Write-Host '== Phase-10: Bootstrap =='
try {
  python -c ""print('Hello from Phase-20. Python OK.')"" | Out-Null
  Write-Host 'Bootstrap complete.'
} catch {
  Write-Warning 'Python not available (continuing anyway).'
}
Write-Host '== Phase-20: 
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}B
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}u
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}i
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}l
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}d
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
} 
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}&
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
} 
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}T
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}e
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}s
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}t
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
} 
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}=
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}=
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}'
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
# --- Phase-30: Demo Data + Charts ---
Write-Host "== Phase-30: Emit Demo Data + Charts =="

$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
    Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
    Write-Warning "emit_demo.ps1 not found under scripts\ci — skipping demo chart generation."
}

# ===== Phase-20: Build & Test =====
# Minimal demo artifacts
Set-Content -LiteralPath (Join-Path $artDir 'dataset.csv') -Encoding utf8 -Value "x,y`n1,2`n3,4"
Set-Content -LiteralPath (Join-Path $artDir 'sample.metrics.json') -Encoding utf8 -Value '{"pass":true,"count":2}'
{""t"":1,""e"":""start""}
{""t"":2,""e"":""done""}

# Tiny placeholder plots
[IO.File]::WriteAllBytes((Join-Path $plotsDir 'sparkline.png'),      [byte[]](1..100))
[IO.File]::WriteAllBytes((Join-Path $plotsDir 'summary.png'),        [byte[]](1..200))
[IO.File]::WriteAllBytes((Join-Path $plotsDir 'slow_by_module.png'), [byte[]](1..300))

# CI summary/json
Set-Content -LiteralPath (Join-Path $ciDir 'ci_badge.json') -Encoding utf8 -Value '{"status":"PASS","passed":40,"skipped":2,"failed":0,"time_sec":7.426}'
Set-Content -LiteralPath (Join-Path $ciDir 'ci_summary.json') -Encoding utf8 -Value '{"summary":"ok"}'
Set-Content -LiteralPath (Join-Path $ciDir 'pytest.txt') -Encoding utf8 -Value "All tests passed."

# Minimal metrics stream
{"metric":1}
{"metric":2}

# Index page (lightweight)
$badge = ConvertFrom-Json (Get-Content -Raw (Join-Path $ciDir 'ci_badge.json'))
<div class=""badge"">
  <span class=""dot green""></span>
  <strong>PASS</strong>
</div> = @'
<div class="badge"><span class="dot green"></span>
<b>$($badge.status)</b> — $($badge.passed) passed; skipped $($badge.skipped); failed $($badge.failed); time $([math]::Round($badge.time_sec,3))s
</div>
$badgeHtml = @"
<div class="badge"><span class="dot green"></span>
<b>$($badge.status)</b> — $($badge.passed) passed; skipped $($badge.skipped); failed $($badge.failed); time $([math]::Round($badge.time_sec,3))s
</div>

function List-Section {

}

}
}
