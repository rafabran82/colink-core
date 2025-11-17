param(
  [string]$Zip  = (Get-ChildItem -Force . | ? Name -like "ci-artifacts-*.zip" | Sort LastWriteTime -Desc | Select -First 1 -Expand Name),
  [string]$Tgz  = (Get-ChildItem -Force . | ? Name -like "ci-artifacts-*.tgz" | Sort LastWriteTime -Desc | Select -First 1 -Expand Name)
)
$ErrorActionPreference = "Stop"
Set-Location (git rev-parse --show-toplevel)

Write-Host "ZIP list ($Zip):" -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zf = [IO.Compression.ZipFile]::OpenRead((Join-Path $PWD $Zip))
try {
  $zf.Entries | % FullName | ? { $_ -like ".artifacts/*" } | Select-Object -First 20
} finally { $zf.Dispose() }

Write-Host "`nTGZ list ($Tgz):" -ForegroundColor Cyan
tar -tzf (Join-Path $PWD $Tgz) | Select-String -SimpleMatch ".artifacts/" | Select-Object -First 20
