param(
  [string]$RunsDir = ".artifacts\ci\runs",
  [int]$MaxFiles = 100
)

$ErrorActionPreference = "Stop"
$all = Get-ChildItem $RunsDir -Filter "run-summary_*.json" | Sort-Object LastWriteTime -Descending
if ($all.Count -gt $MaxFiles) {
  $remove = $all | Select-Object -Skip $MaxFiles
  $remove | ForEach-Object { Remove-Item $_.FullName -Force }
  Write-Host "♻️  Removed $($remove.Count) old summaries (kept $MaxFiles)"
} else {
  Write-Host "✅ Rotation not needed ($($all.Count) ≤ $MaxFiles)"
}
