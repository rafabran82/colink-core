param()
$ErrorActionPreference = "Stop"
Set-Location (git rev-parse --show-toplevel)

& .\scripts\ci\Phase-10-Bootstrap.ps1
& .\scripts\ci\Phase-20-BuildAndTest.ps1
& .\scripts\ci\Phase-30-Package.ps1

Write-Host "`nAll done. Artifacts:" -ForegroundColor Cyan
Get-ChildItem -Force .artifacts
Write-Host "`nBundles:" -ForegroundColor Cyan
Get-ChildItem -Force ci-artifacts.*
