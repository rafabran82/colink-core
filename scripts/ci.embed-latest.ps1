param(
  [string]$IndexPath,
  [string]$SummaryJson
)

if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} else {
  $scriptDir = Join-Path (Get-Location).Path "scripts"
}
$repoRoot = Split-Path $scriptDir -Parent

if (-not $IndexPath)   { $IndexPath   = Join-Path $repoRoot ".artifacts\index.html" }
if (-not $SummaryJson) { $SummaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json" }

if (-not (Test-Path $SummaryJson)) {
  Write-Warning "No summary.json found at $SummaryJson — skipping embed."
  exit 0
}

try {
  $data = Get-Content $SummaryJson -Raw | ConvertFrom-Json
} catch {
  Write-Warning "Failed to read $SummaryJson: $($_.Exception.Message)"
  exit 0
}

if (-not $data -or $data.Count -eq 0) {
  Write-Warning "Empty summary.json — skipping embed."
  exit 0
}

$latest = $data[-1]
$keys = @("run_id","timestamp_utc","events_count","errors_count","success_rate","latency_ms_p50","latency_ms_p95","latency_ms_max")
$rows = foreach ($k in $keys) {
  if ($latest.PSObject.Properties.Name -contains $k) {
    "<tr><td style='padding:4px 8px;color:#bbb;'>$k</td><td style='padding:4px 8px;color:#fff;'>$($latest.$k)</td></tr>"
  }
}

$snippet = @"
<div style='margin:14px 0;padding:10px;border:1px solid #333;border-radius:10px;background:#1a1a1a'>
  <div style='color:#00D4FF;font-weight:600;margin-bottom:6px;'>Latest Run Metrics</div>
  <table style='border-collapse:collapse;font-family:ui-sans-serif,system-ui,Segoe UI; font-size:12px;'>
    $(($rows -join "`n"))
  </table>
</div>
"@

$marker = "<!-- CI-TREND-CHARTS-BEGIN -->"
if (Test-Path $IndexPath) {
  $html = Get-Content $IndexPath -Raw
  if ($html -match [regex]::Escape($marker)) {
    $html = $html -replace [regex]::Escape($marker), ($snippet + "`n" + $marker)
  } else {
    $html = $snippet + "`n" + $html
  }
  Set-Content -Path $IndexPath -Value $html -Encoding utf8
  Write-Host "✅ Embedded latest metrics into $IndexPath"
} else {
  Write-Warning "Index not found at $IndexPath — skipping embed."
}
