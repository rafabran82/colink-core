param(
  [string]$ArtifactsRoot = ".artifacts",
  [string]$OutCsv = $null
)

$ErrorActionPreference = "Stop"
$ciRuns = Join-Path $ArtifactsRoot "ci\runs"
if (-not $OutCsv) { $OutCsv = Join-Path $ciRuns "runs_log.csv" }

$items = Get-ChildItem $ciRuns -Filter "run-summary_*.json" -File -ErrorAction SilentlyContinue
if (-not $items) { Write-Host "[WARN] No summaries in $ciRuns"; return }

$records = foreach ($f in $items) {
  try {
    $j = Get-Content $f.FullName -Raw | ConvertFrom-Json
    [pscustomobject]@{
      Timestamp = [string]$j.Timestamp
      Files     = [int]$j.Files
      SizeMB    = [double]$j.SizeMB
    }
  } catch { }
}

# Filter invalid rows, de-dupe by Timestamp, order ascending
$records = $records | Where-Object { $_.Timestamp -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}' }
$records = $records | Sort-Object Timestamp -Unique

# Write CSV: Timestamp,Files,SizeMB with invariant decimal dot
$culture = [Globalization.CultureInfo]::InvariantCulture
$lines = $records | ForEach-Object {
  '{0},{1},{2}' -f $_.Timestamp, $_.Files, ($_.SizeMB.ToString('0.###', $culture))
}
$lines | Set-Content -Path $OutCsv -Encoding utf8
Write-Host "✅ Rebuilt CSV at $OutCsv from $($records.Count) summaries."
