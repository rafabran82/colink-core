[CmdletBinding()]
param(
  [ValidateSet("major","minor","patch")] [string]$Part = "patch"
)
$ErrorActionPreference = "Stop"
Write-Host "==> Format & test before release..."
& powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\Format.ps1
& powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\Invoke-Tests.ps1

Write-Host "==> Bump version..."
$new = & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\Bump-Version.ps1 -Part $Part
git add -A
git commit -m "chore: release v$new"
git tag "v$new"
git push
git push --tags
Write-Host "Release v$new pushed."

