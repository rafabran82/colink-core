param()
$ErrorActionPreference = "Stop"
Set-Location (git rev-parse --show-toplevel)

& .\scripts\ci\Phase-10-Bootstrap.ps1
& .\scripts\ci\Phase-20-BuildAndTest.ps1
& .\scripts\ci\Phase-25-EmitSamples.ps1
& .\scripts\ci\Phase-30-Package.ps1
& .\scripts\ci\Make-IndexHtml.ps1

Write-Host "`nAll done. Artifacts:" -ForegroundColor Cyan
Get-ChildItem -Force .artifacts
Write-Host "`nOpen .artifacts\index.html for a browseable summary." -ForegroundColor Cyan
Write-Host "`nBundles:" -ForegroundColor Cyan
Get-ChildItem -Force ci-artifacts.*
