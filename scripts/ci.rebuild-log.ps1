param([string]$ArtifactsRoot = ".artifacts",[string]$OutCsv = $null)

$ErrorActionPreference = "Stop"
$ciRuns = Join-Path $ArtifactsRoot "ci\runs"
if (-not $OutCsv){ $OutCsv = Join-Path $ciRuns "runs_log.csv" }

$items = Get-ChildItem $ciRuns -Filter "run-summary_*.json" -File -ErrorAction SilentlyContinue
if (-not $items){ Write-Host "[WARN] No summaries in $ciRuns"; return }

function Normalize-Timestamp([string]$raw) {
  if (-not $raw) { return $null }
  # 1) ISO with 'T'
  if ($raw -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$') { return $raw }
  # 2) ISO with space
  if ($raw -match '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$') { return ($raw -replace ' ', 'T') }
  # 3) run_id like 20251111-105515
  if ($raw -match '^\d{8}-\d{6}$') {
    $y=$raw.Substring(0,4); $m=$raw.Substring(4,2); $d=$raw.Substring(6,2)
    $H=$raw.Substring(9,2); $M=$raw.Substring(11,2); $S=$raw.Substring(13,2)
    return "$y-$m-$d`T$H`:$M`:$S"
  }
  return $null
}

$parsed = @()
foreach ($f in $items) {
  try {
    $j = Get-Content $f.FullName -Raw | ConvertFrom-Json

    # timestamp: prefer new 'Timestamp', else legacy 'timestamp', else fallback to 'run_id'
    $rawTs = $null
    if ($null -ne $j.Timestamp) { $rawTs = [string]$j.Timestamp }
    elseif ($null -ne $j.timestamp) { $rawTs = [string]$j.timestamp }
    elseif ($null -ne $j.run_id)    { $rawTs = [string]$j.run_id }

    $ts = Normalize-Timestamp $rawTs
    if (-not $ts) { continue }

    # files: new 'Files' or legacy 'artifacts'
    $files = $null
    if ($null -ne $j.Files)      { $files = [int]$j.Files }
    elseif ($null -ne $j.artifacts) { $files = [int]$j.artifacts }
    else { $files = 0 }

    # size: new 'SizeMB' or legacy 'size_mb'
    $mb = $null
    if ($null -ne $j.SizeMB)     { $mb = [double]$j.SizeMB }
    elseif ($null -ne $j.size_mb){ $mb = [double]$j.size_mb }
    else { $mb = 0.0 }

    $parsed += [pscustomobject]@{ Timestamp=$ts; Files=$files; SizeMB=$mb }
  } catch {
    Write-Host "[WARN] Failed to parse $($f.Name): $($_.Exception.Message)"
  }
}

if (-not $parsed) {
  Write-Host "[WARN] Parsed 0 summaries; leaving existing CSV untouched: $OutCsv"
  return
}

# de-dupe + sort
$parsed = $parsed | Sort-Object Timestamp -Unique

# write CSV with invariant decimal dot
$c = [Globalization.CultureInfo]::InvariantCulture
$lines = $parsed | ForEach-Object { '{0},{1},{2}' -f $_.Timestamp, $_.Files, ($_.SizeMB.ToString('0.###', $c)) }
$lines | Set-Content -Path $OutCsv -Encoding utf8
Write-Host "✅ Rebuilt CSV at $OutCsv from $($parsed.Count) summaries."
