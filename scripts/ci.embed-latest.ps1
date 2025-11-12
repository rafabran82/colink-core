param(
  [string] $IndexPath   = ".artifacts\index.html",
  [string] $SummaryJson = ".artifacts\metrics\summary.json",
  [string] $SummaryCsv  = ".artifacts\metrics\summary.csv",
  [string] $DeltaJson   = ".artifacts\metrics\delta.json",
  [switch] $Quiet
)

function _nz([object]$x) {
  if ($null -eq $x) { return "" }
  return [string]$x
}

function Get-Field {
  param(
    [Parameter(Mandatory)]$Obj,
    [string[]]$Names
  )
  if ($null -eq $Obj) { return $null }

  # Prefer first item if a sequence (but not string/hashtable)
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
      if ($Obj -is [hashtable]) {
        if ($Obj.ContainsKey($n)) { return $Obj[$n] }
        $k = $Obj.Keys | Where-Object { $_ -like $n } | Select-Object -First 1
        if ($k) { return $Obj[$k] }
      }
    }
  }
  return $null
}

# --- Load summary (JSON, else CSV) ---
$summaryObj = $null
if (Test-Path $SummaryJson) {
  try { $summaryObj = Get-Content $SummaryJson -Raw | ConvertFrom-Json } catch { $summaryObj = $null }
}
if ($null -eq $summaryObj -and (Test-Path $SummaryCsv)) {
  try {
    $csv = Import-Csv $SummaryCsv
    if ($csv.Count -gt 0) { $summaryObj = $csv | Select-Object -First 1 }
  } catch { $summaryObj = $null }
}

if (-not $summaryObj) {
  if (-not $Quiet) { Write-Warning "No metrics summary found (checked JSON then CSV). Skipping embed." }
  return
}

# Optional delta
$deltaObj = $null
if (Test-Path $DeltaJson) {
  try { $deltaObj = Get-Content $DeltaJson -Raw | ConvertFrom-Json } catch { $deltaObj = $null }
}

# --- Extract fields safely ---
$totalMb = Get-Field -Obj $summaryObj -Names @('TotalMB','TotalMb','total_mb','TotalMBs','Total_Mb')
$files   = Get-Field -Obj $summaryObj -Names @('Files','file_count','Count','NumFiles','files')
$ts      = Get-Field -Obj $summaryObj -Names @('Timestamp','RunTimestamp','Generated','time','RunTs')

$deltaMb   = if ($deltaObj) { Get-Field -Obj $deltaObj -Names @('DeltaMB','DeltaMb','delta_mb') } else { $null }
$deltaFiles= if ($deltaObj) { Get-Field -Obj $deltaObj -Names @('DeltaFiles','delta_files','FilesDelta') } else { $null }

$totalMbStr = (_nz $totalMb)
$filesStr   = (_nz $files)
$tsStr      = (_nz $ts)
$deltaMbStr = (_nz $deltaMb)
$deltaFStr  = (_nz $deltaFiles)

# --- Build badge HTML (field-safe) ---
$badge = @"
<div id="ci-latest-metrics" style="font-family:system-ui,Segoe UI,Arial,sans-serif;margin:8px 0;padding:10px 12px;border:1px solid #e5e7eb;border-radius:10px;display:inline-block">
  <span style="font-weight:600">Latest CI:</span>
  <span>Total MB = <code>$totalMbStr</code></span>,
  <span>Files = <code>$filesStr</code></span>
  $(if ($tsStr) { "<span style='color:#6b7280'>&nbsp;•&nbsp;$tsStr</span>" })
  $(if ($deltaMbStr -or $deltaFStr) { "<span style='color:#059669'>&nbsp;ΔMB=$deltaMbStr ΔFiles=$deltaFStr</span>" })
</div>
"@

# --- Ensure index.html exists ---
if (-not (Test-Path $IndexPath)) {
  New-Item -ItemType Directory -Force -Path (Split-Path $IndexPath) | Out-Null
  Set-Content -Path $IndexPath -Encoding utf8 -Value "<!doctype html><meta charset='utf-8'><title>Local CI Summary</title><body></body>"
}

# --- Insert or replace between markers ---
$begin = "<!-- METRICS BADGE BEGIN -->"
$end   = "<!-- METRICS BADGE END -->"
$html  = Get-Content $IndexPath -Raw

if ($html -match [regex]::Escape($begin) -and $html -match [regex]::Escape($end)) {
  $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
  $html = [regex]::Replace($html, $pattern, { param($m) "$begin`r`n$badge`r`n$end" }, 'Singleline')
} else {
  $html += "`r`n$begin`r`n$badge`r`n$end"
}

Set-Content -Path $IndexPath -Encoding utf8 -Value $html

if (-not $Quiet) { Write-Host "✅ Embedded latest metrics into $IndexPath" }
