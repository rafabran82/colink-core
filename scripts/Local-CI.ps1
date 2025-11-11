param(
  [switch]$NoOpen,
  [string]$TimeZone = 'Local'
)
$ErrorActionPreference = 'Stop'

Write-Host "`n🚀 Starting Local CI..."

# --- Paths/Meta
$root = (Get-Location).Path
$art  = Join-Path $root ".artifacts"
$runs = Join-Path $art  "ci\runs"
$meta = [ordered]@{
  IndexPath = (Join-Path $art "index.html")
  RunsDir   = $runs
  LogPath   = (Join-Path $runs "runs_log.csv")
  TrendPng  = (Join-Path $runs "runs_trend.png")
}

# --- Phase 1: Append new run summary (already existing code elsewhere)
# (Assume your prior logic writing run-summary_*.json and appending to runs_log.csv lives here.)

# For brevity we only guarantee downstream phases are compatible.

# --- Phase 2: Plot (with optional TZ)
$logForPlot = $meta.LogPath
if ($TimeZone -and $TimeZone -ne 'Local') {
  $tmpCsv = Join-Path ([IO.Path]::GetTempPath()) ("runs_log_{0}.csv" -f ($TimeZone -replace '\s',''))
  & "$PSScriptRoot\ci.tz-convert.ps1" -InCsv $meta.LogPath -OutCsv $tmpCsv -TimeZone $TimeZone
  $logForPlot = $tmpCsv
}

& python "scripts/ci.plot.py" --log "$logForPlot" 2>&1 | ForEach-Object { Write-Host $_ }

# --- Phase 3: Build "Last 5 Runs" table (with TZ + badge)
$last5 = & "$PSScriptRoot\ci.table.ps1" -RunsLog $meta.LogPath -Count 5 -TimeZone $TimeZone

# --- Phase 4: Embed HTML + footer hint
$footer = "<p style='font-size:12px;color:#555;margin-top:16px'>Tip: Use <code>rebuild_ci.cmd</code> to refresh the summary and chart without adding a new run.</p>"
& "$PSScriptRoot\ci.embed.ps1" -IndexPath $meta.IndexPath -ChartRelPath "ci/runs/runs_trend.png" -ExtraHtml $last5 -FooterHtml $footer

# --- Phase 5: Rotate summaries (keep 100)
& "$PSScriptRoot\ci.rotate.ps1" -RunsDir $meta.RunsDir -MaxFiles 100

# --- Phase 6: Browser
if (-not $NoOpen) {
  Write-Host "🌐 Opening index.html..."
  Start-Process $meta.IndexPath
} else {
  Write-Host "🧩 -NoOpen flag detected; skipping browser launch."
}

Write-Host "`n🏁 Local CI complete."
