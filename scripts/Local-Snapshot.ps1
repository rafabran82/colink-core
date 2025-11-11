param(
  [string]$Note = "",
  [int]$Keep = 10
)

$ErrorActionPreference = "Stop"

function Remove-OldFiles {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Filter,
    [int]$Keep = 10
  )
  if (!(Test-Path $Dir)) { return }
  Get-ChildItem -Path $Dir -Filter $Filter -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Keep |
    Remove-Item -Force -ErrorAction SilentlyContinue
}

function Move-WithRetry {
  param(
    [Parameter(Mandatory=$true)][string]$Src,
    [Parameter(Mandatory=$true)][string]$Dst,
    [int]$Attempts = 6,
    [int]$DelayMs  = 300
  )
  for ($i = 1; $i -le $Attempts; $i++) {
    try {
      Move-Item -Force -LiteralPath $Src -Destination $Dst
      return
    } catch {
      if ($i -eq $Attempts) { throw }
      Start-Sleep -Milliseconds $DelayMs
    }
  }
}

# Resolve repo root (git if available; else CWD)
$root = (git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
Set-Location -LiteralPath $root

# Compose names
$ts    = Get-Date -Format 'yyyyMMdd_HHmmss'
$short = (git rev-parse --short HEAD 2>$null)
if (-not $short) { $short = 'nogit' }
$tag   = if ($Note) { "$short-$Note" } else { $short }

# Prepare paths
$destDir = Join-Path $root '.local_snapshots'
$tmp     = Join-Path $env:TEMP ("snapshot_{0}_{1}.zip" -f $ts,$tag)
$final   = Join-Path $destDir ("snapshot_{0}_{1}.zip" -f $ts,$tag)

if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }

# Collect items (exclude heavy/dev folders)
$items = Get-ChildItem -Force -Name |
           Where-Object { $_ -notin @('.git', '.venv') }

# Make zip in temp, then atomically move
if (Test-Path $tmp)   { Remove-Item -Force $tmp }
if (Test-Path $final) { Remove-Item -Force $final }

Compress-Archive -Path $items -DestinationPath $tmp -CompressionLevel Optimal -Force
Move-WithRetry -Src $tmp -Dst $final

Write-Host "Created snapshot: $final"

# Retain only latest $Keep snapshots
Remove-OldFiles -Dir $destDir -Filter 'snapshot_*.zip' -Keep $Keep
