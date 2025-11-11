# scripts/ci.tz.convert.ps1
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$InCsv,
  [Parameter(Mandatory=$true)][string]$ToTz,
  [string]$TimeColumn = "timestamp"
)
$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"

function Resolve-TimeZone {
  param([string]$LabelOrId)
  $map = @{
    'LOCAL'    = 'LOCAL'
    'EASTERN'  = 'Eastern Standard Time'
    'CENTRAL'  = 'Central Standard Time'
    'MOUNTAIN' = 'Mountain Standard Time'
    'PACIFIC'  = 'Pacific Standard Time'
    'UTC'      = 'UTC'
  }
  $key = $LabelOrId.Trim().ToUpperInvariant()
  if ($map.ContainsKey($key)) { if ($map[$key] -eq 'LOCAL') { return [TimeZoneInfo]::Local }; return [TimeZoneInfo]::FindSystemTimeZoneById($map[$key]) }
  return [TimeZoneInfo]::FindSystemTimeZoneById($LabelOrId)
}

function Parse-Date {
  param([string]$s)
  try { return [DateTimeOffset]::Parse($s) } catch {}
  $dt = [DateTime]::Parse($s)
  if ($dt.Kind -eq [DateTimeKind]::Unspecified) { $dt = [DateTime]::SpecifyKind($dt, [DateTimeKind]::Local) }
  [DateTimeOffset]::new($dt)
}

# --- Load CSV robustly (supports headerless files)
$inAbs = (Resolve-Path -LiteralPath $InCsv).Path
if (-not (Test-Path -LiteralPath $inAbs)) { throw "Input CSV not found: $inAbs" }

# Peek first line to decide if it's headerless
$firstLine = (Get-Content -LiteralPath $inAbs -TotalCount 1)
# split by comma; trim
$parts = $firstLine -split ',' | ForEach-Object { $_.Trim() }

$isoRx = '^\d{4}-\d{2}-\d{2}T'
$looksLikeDataRow =
    ($parts | Where-Object { $_ -match $isoRx }).Count -gt 0 -or
    ($parts | Where-Object { $_ -match '^[\d\.\-]+$' }).Count -ge [math]::Max(2, [int]([double]$parts.Count * 0.66))

if ($looksLikeDataRow) {
  # headerless → synthesize headers
  $colCount = $parts.Count
  $headers = @()
  for ($i=0; $i -lt $colCount; $i++) {
    if ($i -eq 0) { $headers += 'timestamp' } else { $headers += ('metric{0}' -f $i) }
  }
  $rows = Import-Csv -LiteralPath $inAbs -Header $headers
} else {
  $rows = Import-Csv -LiteralPath $inAbs
}

if (-not $rows -or $rows.Count -eq 0) {
  # passthrough empty
  $dir  = [IO.Path]::GetDirectoryName($inAbs)
  $base = [IO.Path]::GetFileNameWithoutExtension($inAbs)
  $safe = ($ToTz -replace '[^A-Za-z0-9_-]','_')
  $out  = [IO.Path]::Combine($dir, ("{0}_{1}.csv" -f $base, $safe))
  Copy-Item -LiteralPath $inAbs -Destination $out -Force
  [Console]::Out.WriteLine($out); exit 0
}

# pick a time column if the provided one doesn't exist
$cols = $rows[0].PSObject.Properties.Name
if (-not $cols.Contains($TimeColumn)) {
  $cands = @('timestamp','time','created_at','datetime','date','run_time')
  $picked = ($cands | Where-Object { $cols -contains $_ } | Select-Object -First 1)
  if (-not $picked) { $picked = $cols[0] }  # fall back to first column
  $TimeColumn = $picked
}

$targetTzi = Resolve-TimeZone $ToTz

$dir  = [IO.Path]::GetDirectoryName($inAbs)
$base = [IO.Path]::GetFileNameWithoutExtension($inAbs)
$safe = ($ToTz -replace '[^A-Za-z0-9_-]','_')
$out  = [IO.Path]::Combine($dir, ("{0}_{1}.csv" -f $base, $safe))

$converted = foreach ($r in $rows) {
  $dto = Parse-Date -s $r.$TimeColumn
  $utc = $dto.ToUniversalTime()
  $tzdt = [TimeZoneInfo]::ConvertTimeFromUtc($utc.DateTime, $targetTzi)
  $nr = [ordered]@{}
  foreach ($p in $cols) { $nr[$p] = $r.$p }
  $nr[$TimeColumn] = $tzdt.ToString('s')
  [PSCustomObject]$nr
}

$converted | Export-Csv -NoTypeInformation -LiteralPath $out
[Console]::Out.WriteLine($out)
