param(
  [switch]$NoOpen,
  [string]$ArtifactsRoot = ".artifacts"
)

$ErrorActionPreference = "Stop"
Write-Host "`n🚀 Starting Local CI..." -ForegroundColor Cyan

# 1) Summary (JSON + CSV)
$meta = & scripts\ci.summary.ps1 -ArtifactsRoot $ArtifactsRoot

# 2) Plot (dual-axis; ASCII-only prints)
Write-Host "📈 Generating CI trend chart..." -ForegroundColor Yellow
& python "scripts\ci.plot.py" 2>&1 | ForEach-Object { Write-Host $_ }

# 3) Embed HTML
& scripts\ci.embed.ps1 -IndexPath $meta.IndexPath -ChartRelPath "ci/runs/runs_trend.png"

# 4) Rotate old summaries (keep 100)
& scripts\ci.rotate.ps1 -RunsDir $meta.RunsDir -MaxFiles 100

# 5) Optional browser
if (-not $NoOpen) {
  Write-Host "🌐 Opening index.html..."
  Start-Process $meta.IndexPath
} else {
  Write-Host "🧩 -NoOpen flag detected; skipping browser launch."
}

Write-Host "`n🏁 Local CI complete." -ForegroundColor Cyan
