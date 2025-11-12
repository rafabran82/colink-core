param(
  [string]$IndexPath    = ".artifacts\index.html",
  [string]$SummaryJson  = ".artifacts\metrics\summary.json",
  [string]$SummaryCsv   = ".artifacts\metrics\summary.csv",
  [string]$RunsLogCsv   = ".artifacts\ci\runs\runs_log.csv",
  [switch]$Quiet
)

# --- Helpers: field-safe escaping (HTML + attribute safe) ---
function Escape-HTML {
param(
  [string]$IndexPath = ".artifacts\index.html",
  [string]$SummaryJson = ".artifacts\metrics\summary.json",
  [string]$DeltaJson = ".artifacts\metrics\delta.json",
  [switch]$Quiet
)
function _say([string]$m){ if (-not $Quiet) { Write-Host $m } }
function _warn([string]$m){ Write-Warning $m }
  if ($null -eq $s) { return "" }
  $s = $s -replace '&','&amp;'
  $s = $s -replace '<','&lt;'
  $s = $s -replace '>','&gt;'
  $s = $s -replace '"','&quot;'
  $s = $s -replace "'","&#39;"
  return $s
}

# --- Load summary: prefer JSON, fallback to CSV (last row) ---
$summary = $null
if (Test-Path $SummaryJson) {
  try {
    $summary = Get-Content $SummaryJson -Raw | ConvertFrom-Json -ErrorAction Stop
  } catch {
    Write-Warning ("Failed to parse JSON summary at {0}: {1}" -f $SummaryJson, ($_.Exception.Message))
  }
}
if (-not $summary -and (Test-Path $SummaryCsv)) {
  try {
    $rows = Import-Csv $SummaryCsv -ErrorAction Stop
    if ($rows -and $rows.Count -ge 1) { $summary = $rows[-1] }
  } catch {
    Write-Warning ("Failed to parse CSV summary at {0}: {1}" -f $SummaryCsv, ($_.Exception.Message))
  }
}

# Guard: still nothing?
if (-not $summary) {
  Write-Warning "No metrics summary found (checked JSON then CSV). Skipping embed."
  exit 0
}

# --- Build an ordered view of key fields (dynamic; schema-agnostic) ---
$props = @{}

# Prefer these if present (in this order)
$prefer = @(
  'run_id','branch','sha',
  'runs','success','fail','errors',
  'duration_ms','duration_s',
  'files','size_kb','size_mb','total_mb',
  'timestamp','when','tz'
)

foreach ($k in $prefer) {
  if ($summary.PSObject.Properties.Name -contains $k) { $props[$k] = $summary.$k }
}

# Augment from runs_log.csv (adds Files/TotalMB/RunTimestamp + overall Runs)
if (Test-Path $RunsLogCsv) {
  try {
    $logRows = Import-Csv $RunsLogCsv -ErrorAction Stop
    if ($logRows -and $logRows.Count -ge 1) {
      $last = $logRows[-1]
      # Common column names from our charts
      if (-not $props.ContainsKey('files')     -and $last.PSObject.Properties.Name -contains 'Files')     { $props['files'] = $last.Files }
      if (-not $props.ContainsKey('total_mb')  -and $last.PSObject.Properties.Name -contains 'TotalMB')   { $props['total_mb'] = $last.TotalMB }
      if (-not $props.ContainsKey('timestamp') -and $last.PSObject.Properties.Name -contains 'RunTimestamp') { $props['timestamp'] = $last.RunTimestamp }
      if (-not $props.ContainsKey('runs')) { $props['runs'] = $logRows.Count }
    }
  } catch {
    Write-Warning ("Failed to read runs log at {0}: {1}" -f $RunsLogCsv, ($_.Exception.Message))
  }
}

# Fill up to 8 fields with anything else available
foreach ($p in $summary.PSObject.Properties) {
  if ($props.ContainsKey($p.Name)) { continue }
  if ($props.Count -ge 8) { break }
  $props[$p.Name] = $p.Value
}

# Render kv spans
$kvSpans = @()
foreach ($k in $props.Keys) {
  $v = $props[$k]
  if ($null -eq $v) { continue }
  $vk = Escape-HTML ([string]$k)
  $vv = Escape-HTML ([string]$v)
  $kvSpans += "<span class='kv' style='padding:.15rem .45rem;border-radius:.6rem;background:#f8fafc;border:1px solid #e5e7eb'><b>$vk</b>: $vv</span>"
}

if ($kvSpans.Count -eq 0) {
  Write-Warning "Summary loaded but had no printable fields. Skipping embed."
  exit 0
}

# Compose badge block
$badge = @"
<div id='metrics-badge' style='display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;padding:.6rem .8rem;border-radius:1rem;border:1px solid #e5e7eb;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Ubuntu,"Helvetica Neue",Arial,"Noto Sans","Apple Color Emoji","Segoe UI Emoji";font-size:.9rem;'>
  <span class='dot' style='width:.6rem;height:.6rem;border-radius:9999px;background:#10b981;display:inline-block' title='Healthy'></span>
  <span class='label' style='font-weight:600;margin-right:.1rem'>Latest CI</span>
  $(($kvSpans -join "`n  "))
</div>
"@

# Ensure index exists
if (-not (Test-Path $IndexPath)) {
  New-Item -ItemType File -Force -Path $IndexPath | Out-Null
  Set-Content -Path $IndexPath -Encoding utf8 -Value "<!doctype html><meta charset='utf-8'><title>COLINK CI</title>`n<body></body>"
}

# Replace or append between markers, but only write if changed (no-op optimization)
$html  = Get-Content $IndexPath -Raw -ErrorAction Stop
$begin = '<!-- METRICS BADGE BEGIN -->'
$end   = '<!-- METRICS BADGE END -->'
$newBlock = "$begin`r`n$badge`r`n$end"

$updated = $false
if ($html -match [regex]::Escape($begin) -and $html -match [regex]::Escape($end)) {
  $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
  $currentBlock = ([regex]::Match($html, $pattern, 'Singleline')).Value
  if ($currentBlock -ne $newBlock) {
    $html = [regex]::Replace($html, $pattern, { param($m) $newBlock }, 'Singleline')
    $updated = $true
  }
} else {
  if ($html -notmatch '</body>') {
    $html += "`r`n$newBlock"
  } else {
    $html = $html -replace '</body>', "$newBlock`r`n</body>"
  }
  $updated = $true
}

if ($updated) {
  Set-Content -Path $IndexPath -Encoding utf8 -Value $html
  if (-not $Quiet) { Write-Host "✅ Embedded latest metrics into $IndexPath" }
} else {
  if (-not $Quiet) { Write-Host "ℹ️ Metrics badge already up to date — no changes written." }
}


