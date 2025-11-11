param([string]$ArtifactsRoot = ".artifacts")

$ErrorActionPreference = "Stop"

# Paths
$runsDir   = Join-Path $ArtifactsRoot "ci\runs"
$indexPath = Join-Path $ArtifactsRoot "index.html"
$logPath   = Join-Path $runsDir "runs_log.csv"

# 1) Rebuild the CSV from JSON summaries
& scripts\ci.rebuild-log.ps1 -ArtifactsRoot $ArtifactsRoot

# 2) Re-generate the chart (ASCII-only prints)
& python "scripts\ci.plot.py" 2>&1 | ForEach-Object { Write-Host $_ }

# 3) Build "Last 5 Runs" table
$last5 = & scripts\ci.table.ps1 -RunsLog $logPath -Count 5

# 4) Re-embed HTML (chart + table)
& scripts\ci.embed.ps1 -IndexPath $indexPath -ChartRelPath "ci/runs/runs_trend.png" -ExtraHtml $last5

Write-Host "`n✅ Rebuild + refresh complete (no new run created)." -ForegroundColor Green
