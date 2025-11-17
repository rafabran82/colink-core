param(
  [Parameter(Mandatory=$true)][string]$S3Uri
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
  throw "AWS CLI not found. Install and run 'aws configure' first."
}
$zip = Join-Path $PWD "ci-artifacts.zip"
$tgz = Join-Path $PWD "ci-artifacts.tgz"
if (-not (Test-Path $zip) -or -not (Test-Path $tgz)) { throw "Missing bundles; run Run-All.ps1 first." }

aws s3 cp $zip $S3Uri
aws s3 cp $tgz $S3Uri
Write-Host "Uploaded to $S3Uri" -ForegroundColor Green
