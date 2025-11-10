param()
$ErrorActionPreference = "Stop"

Write-Host "== Phase-30: Package artifacts ==" -ForegroundColor Cyan

$art = Join-Path $PWD ".artifacts"
if (-not (Test-Path $art)) { New-Item -ItemType Directory -Force -Path $art | Out-Null }

# Manifest
$manifest = [ordered]@{
  commit    = (git rev-parse HEAD 2>$null)
  when      = (Get-Date).ToString("s")
  machine   = $env:COMPUTERNAME
  runner    = "local"
  python    = (& (Join-Path $PWD ".venv\Scripts\python.exe") -c "import sys;print(sys.version)" 2>$null)
  notes     = "Local CI manifest"
  files     = (Get-ChildItem -Path $art -File -Recurse | ForEach-Object { $_.FullName })
}
($manifest | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $art "ci.manifest.json") -Encoding utf8

# ZIP
$zip = Join-Path $PWD "ci-artifacts.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $art "*") -DestinationPath $zip -Force

# TGZ via tar (Windows 10+ includes bsdtar as 'tar')
$tgz = Join-Path $PWD "ci-artifacts.tgz"
if (Test-Path $tgz) { Remove-Item $tgz -Force }
tar -czf $tgz -C $PWD ".artifacts"

Write-Host "Created:`n  $zip`n  $tgz" -ForegroundColor Green
