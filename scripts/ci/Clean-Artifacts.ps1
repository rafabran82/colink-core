param([int]$Keep = 5)
$ErrorActionPreference = "Stop"
Set-Location (git rev-parse --show-toplevel)

$bundles = Get-ChildItem -Force . | ? Name -like "ci-artifacts-*.*" | Sort LastWriteTime -Desc
$bundlesToRemove = $bundles | Select-Object -Skip $Keep
if ($bundlesToRemove) {
  Write-Host "Removing old bundles:" -ForegroundColor Yellow
  $bundlesToRemove | % { $_.FullName } | Write-Host
  $bundlesToRemove | Remove-Item -Force
} else {
  Write-Host "Nothing to remove; $((($bundles).Count)) bundles ≤ Keep=$Keep" -ForegroundColor Green
}
