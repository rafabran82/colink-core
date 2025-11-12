param(
  [Parameter(Mandatory=$true)] [string]$IndexPath,
  [Parameter(Mandatory=$true)] [string]$SummaryJson,
  [string]$DeltaJson = ""
)

function Read-Json($p) {
  if (-not (Test-Path $p)) { return $null }
  try { return Get-Content $p -Raw | ConvertFrom-Json -Depth 4 } catch { return $null }
}

try {
  $summary = Read-Json $SummaryJson
} catch {
  Write-Warning "Failed to read ${SummaryJson}: $($_.Exception.Message)"
  exit 0
}

if (-not $summary) { Write-Warning "No summary data"; exit 0 }

# Normalize rows
if ($summary.PSObject.Properties.Name -contains "rows") { $rows = $summary.rows } else { $rows = $summary }
if (-not $rows -or $rows.Count -lt 1) { Write-Warning "No rows in summary"; exit 0 }

$cur = $rows[-1]
$ts  = $cur.ts
if (-not $ts) { $ts = $cur.timestamp }

# Try to read deltas if available
$delta = $null
if ($DeltaJson -and (Test-Path $DeltaJson)) {
  $delta = Read-Json $DeltaJson
}

# Build Latest metrics HTML
$latestLines = @()
foreach ($kv in $cur.PSObject.Properties) {
  $k = $kv.Name; $v = $kv.Value
  if ($k -in @("ts","timestamp")) { continue }
  $latestLines += "<div class='metric'><span class='k'>$k</span><span class='v'>$v</span></div>"
}

$deltaHtml = ""
if ($delta -and $delta.items -and $delta.items.Count -gt 0) {
  $badges = @()
  foreach ($it in $delta.items) {
    $arrow = if ($it.improved) { "↑" } else { "↓" }
    $dot   = if ($it.improved) { "🟢" } else { "🔴" }
    $curr  = "$($it.current)$($it.unit)"
    $prev  = "$($it.previous)$($it.unit)"
    $chg   = if ($it.delta -ge 0) { "+$($it.delta)$($it.unit)" } else { "$($it.delta)$($it.unit)" }
    $badges += "<div class='badge'>$dot <b>$($it.label)</b> $arrow <span class='chg'>$chg</span> <span class='prev'>(prev $prev)</span></div>"
  }
  $joined = ($badges -join "`n")
  $deltaHtml = @"
<div class='delta-wrap'>
  <div class='delta-title'>Δ Since previous run</div>
  <div class='delta-badges'>
    $joined
  </div>
</div>
"@
}

$block = @"
<!-- LATEST_METRICS BEGIN -->
<div class='latest-panel'>
  <div class='latest-title'>Latest Run Metrics</div>
  <div class='latest-ts'>timestamp: $ts</div>
  <div class='latest-body'>
    $($latestLines -join "`n")
  </div>
  $deltaHtml
</div>
<style>
.latest-panel {font-family: system-ui,Segoe UI,Arial; max-width: 380px; border:1px solid #e5e7eb; border-radius:12px; padding:12px; margin:12px 0;}
.latest-title {font-weight:700; margin-bottom:2px;}
.latest-ts {color:#6b7280; font-size:12px; margin-bottom:8px;}
.metric {display:flex; justify-content:space-between; font-size:13px; padding:2px 0; border-bottom:1px dashed #f0f0f0;}
.metric .k {color:#374151}
.metric .v {color:#111827}
.delta-wrap{margin-top:8px; padding-top:6px; border-top:1px solid #e5e7eb;}
.delta-title{font-weight:600; font-size:13px; margin-bottom:6px;}
.delta-badges{display:flex; flex-direction:column; gap:4px;}
.badge{font-size:13px;}
.badge .chg{margin:0 6px;}
.badge .prev{color:#6b7280; font-size:12px;}
</style>
<!-- LATEST_METRICS END -->
"@

# Inject into index.html (replace existing block if present)
$html = Get-Content $IndexPath -Raw
$pattern = '(?s)<!-- LATEST_METRICS BEGIN -->.*?<!-- LATEST_METRICS END -->'
if ($html -match $pattern) {
  $html = [regex]::Replace($html, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $block })
} else {
  # insert after <body> if possible
  if ($html -match '<body[^>]*>') {
    $html = $html -replace '(<body[^>]*>)', "`$1`r`n$block`r`n"
  } else {
    $html = $block + "`r`n" + $html
  }
}

Set-Content $IndexPath -Encoding utf8 -Value $html
Write-Host "✅ Embedded latest metrics into $IndexPath"
