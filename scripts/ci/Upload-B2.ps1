param(
  [Parameter(Mandatory=$true)][string]$RemotePath  # e.g., "b2:my-bucket/colink-core/"
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command rclone -ErrorAction SilentlyContinue)) {
  throw "rclone not found. Install and configure a 'b2' remote."
}
$zip = Join-Path $PWD "ci-artifacts.zip"
$tgz = Join-Path $PWD "ci-artifacts.tgz"
if (-not (Test-Path $zip) -or -not (Test-Path $tgz)) { throw "Missing bundles; run Run-All.ps1 first." }

rclone copy $zip $RemotePath
rclone copy $tgz $RemotePath
Write-Host "Uploaded to $RemotePath" -ForegroundColor Green
