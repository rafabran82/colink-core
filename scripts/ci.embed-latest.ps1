param(
  [string]$IndexPath   = ".artifacts\index.html",
  [string]$SummaryJson = ".artifacts\metrics\summary.json",
  [string]$SummaryCsv  = ".artifacts\metrics\summary.csv",
  [string]$DeltaJson   = ".artifacts\metrics\delta.json",
  [switch]$Quiet
)

# -------- helpers --------
function _nz([object]$s) { if ($null -eq $s) { return "" } [string]$s }

function _abs([string]$p) {
  if ([string]::IsNullOrWhiteSpace($p)) { return $p }
  if ([IO.Path]::IsPathRooted($p)) { return $p }
  $repo = Split-Path $PSScriptRoot -Parent
  Join-Path $repo $p
}

function Get-Field {
  param(
    [Parameter(Mandatory)]$Obj,
    [string[]]$Names
  )
  if ($null -eq $Obj) { return $null }

  # If it's an array/collection, prefer the first item (but not for hashtable or string)
  if ($Obj -is [System.Collections.IEnumerable] -and -not ($Obj -is [string]) -and ($Obj -isnot [hashtable])) {
    $Obj = ($Obj | Select-Object -First 1)
  }

  foreach ($n in $Names) {
    try {
      $props   = $Obj.PSObject.Properties
      $matches = $props.Match($n, [System.Management.Automation.MshMemberMatchOptions]::IgnoreCase)
      if ($matches.Count -gt 0) {
        $actual = $matches[0].Name
        return $Obj.$actual
      }
    } catch {
      # If it's a hashtable, try direct key or wildcard-ish match
      if ($Obj -is [hashtable]) {
        if ($Obj.ContainsKey($n)) { return $Obj[$n] }
        $k = $Obj.Keys | Where-Object { param(
  [string]$IndexPath   = ".artifacts\index.html",
  [string]$SummaryJson = ".artifacts\metrics\summary.json",
  [string]$SummaryCsv  = ".artifacts\metrics\summary.csv",
  [string]$DeltaJson   = ".artifacts\metrics\delta.json",
  [switch]$Quiet
)

# -------- helpers --------
function _nz([object]$s) { if ($null -eq $s) { return "" } [string]$s }

function _abs([string]$p) {
  if ([string]::IsNullOrWhiteSpace($p)) { return $p }
  if ([IO.Path]::IsPathRooted($p)) { return $p }
  $repo = Split-Path $PSScriptRoot -Parent
  Join-Path $repo $p
}

function Get-Field {
  param(
    [Parameter(Mandatory)]$Obj,
    [string[]]$Names
  )
  if ($null -eq $Obj) { return $null }
  # If it’s an array, use the first row
  if ($Obj -is [System.Collections.IEnumerable] -and -not ($Obj -is [string])) {
    $Obj = ($Obj | Select-Object -First 1)
  }
  foreach ($n in $Names) {
    $matches = $Obj.PSObject.Properties.Match($n, 'IgnoreCase')
    if ($matches.Count -gt 0) {
      $actual = $matches[0].Name
      return $Obj.$actual
    }
  }
  return $null
}

# -------- normalize paths --------
$IndexPath   = _abs $IndexPath
$SummaryJson = _abs $SummaryJson
$SummaryCsv  = _abs $SummaryCsv
$DeltaJson   = _abs $DeltaJson
$RunsLogCsv  = _abs ".artifacts\ci\runs\runs_log.csv"

# -------- load summary (JSON → CSV → runs_log.csv) --------
$summary = $null
if (Test-Path $SummaryJson) {
  try { $summary = Get-Content $SummaryJson -Raw | ConvertFrom-Json } catch { }
}
if (-not $summary -and (Test-Path $SummaryCsv)) {
  try {
    $rows = Import-Csv $SummaryCsv
    if ($rows) { $summary = $rows | Select-Object -Last 1 }
  } catch { }
}
if (-not $summary -and (Test-Path $RunsLogCsv)) {
  try {
    $summary = Import-Csv $RunsLogCsv | Select-Object -Last 1
  } catch { }
}

# -------- extract fields robustly --------
$files = Get-Field -Obj $summary -Names @('Files','file_count','Count','NumFiles')
$total = Get-Field -Obj $summary -Names @('TotalMB','total_mb','Total','MB','SizeMB')
$stamp = Get-Field -Obj $summary -Names @('RunTimestamp','timestamp','RunTime','Generated','Time')

# final fallback to empty strings (field-safe)
$files = _nz $files
$total = _nz $total
$stamp = _nz $stamp

# -------- build badge --------
$begin = '<!-- METRICS BADGE BEGIN -->'
$end   = '<!-- METRICS BADGE END -->'
$badge = @"
<div id="metrics-badge" style="font:12px/1.4 Consolas,monospace;border:1px solid #ddd;padding:6px 8px;border-radius:6px;display:inline-block;">
  <span><b>Latest CI</b></span>
  <span style="margin-left:10px">Files: <b>$files</b></span>
  <span style="margin-left:10px">Total MB: <b>$total</b></span>
  <span style="margin-left:10px;color:#666">$stamp</span>
</div>
"@

# -------- embed into index.html --------
if (-not (Test-Path $IndexPath)) {
  if (-not $Quiet) { Write-Warning "Index not found: $IndexPath" }
  exit 0
}

$html = Get-Content $IndexPath -Raw
if ($html -match [regex]::Escape($begin) -and $html -match [regex]::Escape($end)) {
  $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
  $html = [regex]::Replace($html, $pattern, { param($m) "$begin`r`n$badge`r`n$end" }, 'Singleline')
} else {
  $html += "`r`n$begin`r`n$badge`r`n$end"
}

Set-Content -Path $IndexPath -Encoding utf8 -Value $html
if (-not $Quiet) { Write-Host "✅ Embedded latest metrics into $IndexPath" }
 -like $n } | Select-Object -First 1
        if ($k) { return $Obj[$k] }
      }
    }
  }
  return $null
}
  # If it’s an array, use the first row
  if ($Obj -is [System.Collections.IEnumerable] -and -not ($Obj -is [string])) {
    $Obj = ($Obj | Select-Object -First 1)
  }
  foreach ($n in $Names) {
    $matches = $Obj.PSObject.Properties.Match($n, 'IgnoreCase')
    if ($matches.Count -gt 0) {
      $actual = $matches[0].Name
      return $Obj.$actual
    }
  }
  return $null
}

# -------- normalize paths --------
$IndexPath   = _abs $IndexPath
$SummaryJson = _abs $SummaryJson
$SummaryCsv  = _abs $SummaryCsv
$DeltaJson   = _abs $DeltaJson
$RunsLogCsv  = _abs ".artifacts\ci\runs\runs_log.csv"

# -------- load summary (JSON → CSV → runs_log.csv) --------
$summary = $null
if (Test-Path $SummaryJson) {
  try { $summary = Get-Content $SummaryJson -Raw | ConvertFrom-Json } catch { }
}
if (-not $summary -and (Test-Path $SummaryCsv)) {
  try {
    $rows = Import-Csv $SummaryCsv
    if ($rows) { $summary = $rows | Select-Object -Last 1 }
  } catch { }
}
if (-not $summary -and (Test-Path $RunsLogCsv)) {
  try {
    $summary = Import-Csv $RunsLogCsv | Select-Object -Last 1
  } catch { }
}

# -------- extract fields robustly --------
$files = Get-Field -Obj $summary -Names @('Files','file_count','Count','NumFiles')
$total = Get-Field -Obj $summary -Names @('TotalMB','total_mb','Total','MB','SizeMB')
$stamp = Get-Field -Obj $summary -Names @('RunTimestamp','timestamp','RunTime','Generated','Time')

# final fallback to empty strings (field-safe)
$files = _nz $files
$total = _nz $total
$stamp = _nz $stamp

# -------- build badge --------
$begin = '<!-- METRICS BADGE BEGIN -->'
$end   = '<!-- METRICS BADGE END -->'
$badge = @"
<div id="metrics-badge" style="font:12px/1.4 Consolas,monospace;border:1px solid #ddd;padding:6px 8px;border-radius:6px;display:inline-block;">
  <span><b>Latest CI</b></span>
  <span style="margin-left:10px">Files: <b>$files</b></span>
  <span style="margin-left:10px">Total MB: <b>$total</b></span>
  <span style="margin-left:10px;color:#666">$stamp</span>
</div>
"@

# -------- embed into index.html --------
if (-not (Test-Path $IndexPath)) {
  if (-not $Quiet) { Write-Warning "Index not found: $IndexPath" }
  exit 0
}

$html = Get-Content $IndexPath -Raw
if ($html -match [regex]::Escape($begin) -and $html -match [regex]::Escape($end)) {
  $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
  $html = [regex]::Replace($html, $pattern, { param($m) "$begin`r`n$badge`r`n$end" }, 'Singleline')
} else {
  $html += "`r`n$begin`r`n$badge`r`n$end"
}

Set-Content -Path $IndexPath -Encoding utf8 -Value $html
if (-not $Quiet) { Write-Host "✅ Embedded latest metrics into $IndexPath" }

