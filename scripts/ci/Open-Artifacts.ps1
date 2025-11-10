param()
$ErrorActionPreference = "Stop"
Set-Location (git rev-parse --show-toplevel)

$idx = Join-Path $PWD ".artifacts\index.html"
if (Test-Path $idx) { Start-Process $idx }

"`nLatest bundles:" | Write-Host -ForegroundColor Cyan
Get-ChildItem -Force . | Where-Object Name -like 'ci-artifacts-*.*' |
  Sort-Object LastWriteTime -Desc | Select-Object -First 5 |
  Format-Table -AutoSize
