param([string]$DestRoot)

$ErrorActionPreference = "Stop"
Set-Location (git rev-parse --show-toplevel)

# Default destination if not provided
if (-not $DestRoot -or $DestRoot.Trim() -eq '') {
  if ($env:OneDrive -and (Test-Path $env:OneDrive)) {
    $DestRoot = Join-Path $env:OneDrive 'Artifacts\colink-core'
  } else {
    $DestRoot = Join-Path $env:USERPROFILE 'Documents\COLINK-CI\colink-core'
  }
}

# Find newest bundle pair
$zip = Get-ChildItem -Force . | Where-Object Name -like 'ci-artifacts-*.zip' | Sort-Object LastWriteTime -Desc | Select-Object -First 1
$tgz = Get-ChildItem -Force . | Where-Object Name -like 'ci-artifacts-*.tgz' | Sort-Object LastWriteTime -Desc | Select-Object -First 1
if (-not $zip -or -not $tgz) { throw "No ci-artifacts-*.zip/tgz found. Run scripts/ci/Run-All.ps1 first." }

# Create a timestamped drop folder
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest  = Join-Path $DestRoot $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null

# Copy bundles and .artifacts
Copy-Item -LiteralPath $zip.FullName -Destination $dest -Force
Copy-Item -LiteralPath $tgz.FullName -Destination $dest -Force
Copy-Item -Recurse -Force -LiteralPath '.artifacts' -Destination $dest

Write-Host "Published to: $dest" -ForegroundColor Green

# QoL: open the browsable index if present
$idx = Join-Path $dest '.artifacts\index.html'
if (Test-Path $idx) { Start-Process $idx }
