param([switch]$NoOpen)

$ErrorActionPreference = "Stop"
Write-Host "`n🚀 Starting Local CI automation..." -ForegroundColor Cyan

# ===== Paths =====
$artifactsRoot = ".artifacts"
$runsDir  = Join-Path $artifactsRoot "ci\runs"
$indexPath = Join-Path $artifactsRoot "index.html"
$logPath   = Join-Path $runsDir "runs_log.csv"
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null

# ===== Phase-90: Run summary =====
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$files     = (Get-ChildItem -Recurse -File | Measure-Object).Count
$bytesSum  = (Get-ChildItem -Recurse -File | Measure-Object Length -Sum).Sum
$sizeMB    = [math]::Round(($bytesSum / 1MB), 3)

$summary = [ordered]@{
  Timestamp = (Get-Date).ToString("s")
  Files     = $files
  SizeMB    = $sizeMB
}
$summaryPath = Join-Path $runsDir "run-summary_$timestamp.json"
($summary | ConvertTo-Json -Depth 5) | Set-Content -Path $summaryPath -Encoding utf8
Write-Host "✅ Artifact summary written: $summaryPath" -ForegroundColor Green

# Append to CSV (invariant decimal dot)
$csvLine = "{0},{1},{2}" -f $summary.Timestamp, $files, ($sizeMB.ToString([Globalization.CultureInfo]::InvariantCulture))
Add-Content -Path $logPath -Value $csvLine -Encoding utf8
Write-Host "🗃️  Appended to $logPath"

# ===== Phase-91: Call persistent Python plotter =====
Write-Host "📈 Generating CI trend chart..." -ForegroundColor Yellow
& python "scripts\ci.plot.py" 2>&1 | ForEach-Object { Write-Host $_ }

# ===== Phase-92: Embed chart =====
$chartHtml = '<img src="ci/runs/runs_trend.png" width="600">'
$html = @"
<html><body style='font-family:Segoe UI,sans-serif'>
<h2>Local CI Summary</h2>
<p>Generated: $(Get-Date)</p>
$chartHtml
</body></html>
"@
Set-Content -Path $indexPath -Value $html -Encoding utf8
Write-Host "✅ Embedded trend chart into $indexPath"

# ===== Phase-97: Browser open =====
if (-not $NoOpen) {
  Write-Host "🌐 Opening index.html..."
  Start-Process $indexPath
} else {
  Write-Host "🧩 -NoOpen flag detected; skipping browser launch."
}

# ===== Phase-98: Rotation (keep 100) =====
$maxFiles = 100
$all = Get-ChildItem $runsDir -Filter "run-summary_*.json" | Sort-Object LastWriteTime -Descending
if ($all.Count -gt $maxFiles) {
  $remove = $all | Select-Object -Skip $maxFiles
  $remove | ForEach-Object { Remove-Item $_.FullName -Force }
  Write-Host "♻️  Removed $($remove.Count) old summaries (kept $maxFiles)"
} else {
  Write-Host "✅ Rotation not needed ($($all.Count) ≤ $maxFiles)"
}

Write-Host "`n🏁 Local CI complete." -ForegroundColor Cyan
