param([string]$ArtifactsRoot = ".artifacts")

$ErrorActionPreference = "Stop"
$runsDir   = Join-Path $ArtifactsRoot "ci\runs"
$indexPath = Join-Path $ArtifactsRoot "index.html"
$logPath   = Join-Path $runsDir "runs_log.csv"
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null

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
Write-Host "✅ Artifact summary written: $summaryPath"

$csvLine = "{0},{1},{2}" -f $summary.Timestamp, $files, ($sizeMB.ToString([Globalization.CultureInfo]::InvariantCulture))
Add-Content -Path $logPath -Value $csvLine -Encoding utf8
Write-Host "🗃️  Appended to $logPath"

# Return metadata to the caller
[pscustomobject]@{
  ArtifactsRoot = $ArtifactsRoot
  RunsDir       = $runsDir
  IndexPath     = $indexPath
  LogPath       = $logPath
  SummaryPath   = $summaryPath
  Timestamp     = $summary.Timestamp
  Files         = $files
  SizeMB        = $sizeMB
}
