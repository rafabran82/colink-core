param(
  [Parameter(Mandatory=$true)] [string]$IndexPath,
  [Parameter(Mandatory=$true)] [string]$SummaryJson,
  [string]$DeltaJson = $(Join-Path (Split-Path $PSScriptRoot -Parent) ".artifacts\metrics\delta.json")
)

function Get-LatestSummaryRow {
  param([string]$JsonPath, [string]$CsvPath)

  # Try JSON first (if exists & non-trivial)
  if (Test-Path $JsonPath -ErrorAction SilentlyContinue) {
    $len = (Get-Item $JsonPath).Length
    if ($len -gt 10) {
      try {
        $data = Get-Content $JsonPath -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($data -is [System.Array]) {
          if ($data.Count -gt 0) { return $data[-1] }
        } elseif ($data) { return $data }
      } catch {
        Write-Verbose "JSON parse failed: $($_.Exception.Message)"
      }
    }
  }

  # Fallback: CSV
  if (Test-Path $CsvPath -ErrorAction SilentlyContinue) {
    try {
      $rows = Import-Csv $CsvPath
      if ($rows -and $rows.Count -gt 0) { return $rows[-1] }
    } catch {
      Write-Verbose "CSV import failed: $($_.Exception.Message)"
    }
  }

  return $null
}

# Resolve repo root and CSV path
$repoRoot   = Split-Path $PSScriptRoot -Parent
$summaryCsv = Join-Path $repoRoot ".artifacts\metrics\summary.csv"

# Load the latest summary row (with CSV fallback)
$row = Get-LatestSummaryRow -JsonPath $SummaryJson -CsvPath $summaryCsv
if (-not $row) {
  Write-Host "ℹ️  No summary data available after JSON+CSV fallback — leaving dashboard unchanged."
  return
}

# Build a small badge (defensively handle missing keys)
$runId   = $row.run_id    | ForEach-Object { $_ }
$ts      = $row.ts        | ForEach-Object { $_ }
$steps   = $row.steps     | ForEach-Object { $_ }
$success = $row.success   | ForEach-Object { $_ }
$uptime  = $row.uptime_ms | ForEach-Object { $_ }

$parts = @()
if ($runId)   { $parts += "Run: $runId" }
if ($ts)      { $parts += "TS: $ts" }
if ($steps)   { $parts += "Steps: $steps" }
if ($success) { $parts += "OK: $success" }
if ($uptime)  { $parts += "Uptime(ms): $uptime" }
if ($parts.Count -eq 0) { $parts = @("Latest metrics updated") }

$badge = "<div id=""latest-metrics"" style=""font:12px/1.3 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; margin:6px 0;"">
  <strong>Latest Run Metrics:</strong> <span>" + [string]::Join(" · ", $parts) + "</span>
</div>"

# Replace or insert between markers in index.html
$begin = '<!-- METRICS-BEGIN -->'
$end   = '<!-- METRICS-END -->'
$html  = Get-Content $IndexPath -Raw

if ($html -match [regex]::Escape($begin) -and $html -match [regex]::Escape($end)) {
  $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
  $html = [regex]::Replace($html, $pattern, { param($m) "$begin`r`n$badge`r`n$end" }, 'Singleline')
} else {
  $html += "`r`n$begin`r`n$badge`r`n$end"
}

Set-Content -Path $IndexPath -Encoding utf8 -Value $html
Write-Host "✅ Embedded latest metrics into $IndexPath"
