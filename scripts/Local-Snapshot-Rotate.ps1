param([int]$Keep=5)
$dir = Join-Path (Get-Location) ".local_snapshots"
if (-not (Test-Path $dir)) { return }
Get-ChildItem $dir -Filter "snapshot_*.zip" -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip $Keep |
  Remove-Item -Force
