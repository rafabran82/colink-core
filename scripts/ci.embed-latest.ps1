param(
  [Parameter(Mandatory=$true)] [string]$IndexPath,
  [Parameter(Mandatory=$true)] [string]$SummaryJson,
  [string]$DeltaJson = $(Join-Path (Split-Path $PSScriptRoot -Parent) ".artifacts\metrics\delta.json")
)

function Get-Prop {
  param([object]$Obj, [string]$Name)
  if (-not $Obj) { return $null }
  if ($Obj -is [hashtable]) { if ($Obj.ContainsKey($Name)) { return $Obj[$Name] } else { return $null } }
  $p = $Obj.PSObject.Properties[$Name]
  if ($p) { return $p.Value } else { return $null }
}

function Get-LatestSummaryRow {
  param([string]$JsonPath, [string]$CsvPath)

  if (Test-Path $JsonPath -ErrorAction SilentlyContinue) {
    $len = (Get-Item $JsonPath).Length
    if ($len -gt 10) {
      try {
        $data = Get-Content $JsonPath -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($data -is [System.Array]) { if ($data.Count -gt 0) { return $data[-1] } }
        elseif ($data) { return $data }
      } catch { Write-Verbose "JSON parse failed: $($_.Exception.Message)" }
    }
  }

  if (Test-Path $CsvPath -ErrorAction SilentlyContinue) {
    try {
      $rows = Import-Csv $CsvPath
      if ($rows -and $rows.Count -gt 0) { return $rows[-1] }
    } catch { Write-Verbose "CSV import failed: $($_.Exception.Message)" }
  }
  return $null
}

$repoRoot   = Split-Path $PSScriptRoot -Parent
$summaryCsv = Join-Path $repoRoot ".artifacts\metrics\summary.csv"

$row = Get-LatestSummaryRow -JsonPath $SummaryJson -CsvPath $summaryCsv
if (-not $row) {
  Write-Host "ℹ️  No summary data available after JSON+CSV fallback — leaving dashboard unchanged."
  return
}

$fields = @(
  @{ Label = 'Run';         Name = 'run_id' },
  @{ Label = 'TS';          Name = 'ts' },
  @{ Label = 'Steps';       Name = 'steps' },
  @{ Label = 'OK';          Name = 'success' },
  @{ Label = 'Uptime(ms)';  Name = 'uptime_ms' },
  @{ Label = 'Avg Lat(ms)'; Name = 'avg_latency_ms' },
  @{ Label = 'P95(ms)';     Name = 'latency_ms_p95' },
  @{ Label = 'P50(ms)';     Name = 'latency_ms_p50' },
  @{ Label = 'Max(ms)';     Name = 'latency_ms_max' }
)

$parts = New-Object System.Collections.Generic.List[string]
foreach ($f in $fields) {
  $v = Get-Prop -Obj $row -Name $f.Name
  if ($null -ne $v -and "$v".Trim() -ne '') {
    [void]$parts.Add(("{0}: {1}" -f $f.Label, $v))
  }
}
if ($parts.Count -eq 0) { [void]$parts.Add("Latest metrics updated") }

$badge = "<div id=""latest-metrics"" style=""font:12px/1.3 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; margin:6px 0;"">
  <strong>Latest Run Metrics:</strong> <span>" + [string]::Join(" · ", $parts) + "</span>
</div>"

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
