[CmdletBinding()]
param(
  [string]$BootstrapDir = ".artifacts/data/bootstrap",
  [string]$SummaryJson  = ".artifacts/ci/bootstrap.summary.json",
  [string]$RunsCsv      = ".artifacts/ci/runs_log.csv",
  [switch]$ForcePSFallback
)
$ErrorActionPreference = "Stop"

function New-JsonSummary([string]$folder, [hashtable]$present, [int]$txLines, [string]$note, [bool]$ok) {
  [ordered]@{
    ok      = $ok
    ts      = [DateTime]::UtcNow.ToString("o")
    folder  = $folder
    present = $present
    counts  = @{ tx_log_lines = $txLines }
    notes   = @($note)
  } | ConvertTo-Json -Depth 6
}

# Ensure dirs
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SummaryJson) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RunsCsv) | Out-Null

# Helper: PS-only scan of folder
function Get-PSSummary([string]$folder) {
  $targets = @(
    "wallets.json","trustlines.json","offers.json","tx_log.ndjson",
    "bootstrap_meta.json","bootstrap_plan_testnet.json",
    "bootstrap_result_testnet.json","bootstrap_summary_testnet.txt"
  )
  $present = @{}
  foreach ($t in $targets) { $present[$t] = Test-Path (Join-Path $folder $t) }
  $tx = Join-Path $folder "tx_log.ndjson"
  $txLines = (Test-Path $tx) ? ((Get-Content $tx -ErrorAction SilentlyContinue | Where-Object { $_.Trim() }).Count) : 0
  $json = New-JsonSummary $folder $present $txLines "ps-fallback: presence + tx ndjson line count" ($present.Values -contains $true)
  return $json
}

# Try Python verifier unless forced PS
$jsonOut = $null
if (-not $ForcePSFallback) {
  try {
    $temp = New-TemporaryFile
    python "scripts/xrpl.bootstrap.verify.py" "$BootstrapDir" *> $temp.FullName
    $raw = Get-Content $temp.FullName -Raw
    Remove-Item $temp -Force
    # Extract last JSON object if any
    $start = $raw.LastIndexOf('{'); $end = $raw.LastIndexOf('}')
    if ($start -ge 0 -and $end -ge $start) {
      $jsonOut = $raw.Substring($start, $end - $start + 1)
    } else {
      Write-Warning "Python verifier produced no JSON; using PS fallback."
    }
  } catch {
    Write-Warning "Python verifier failed: $($_.Exception.Message); using PS fallback."
  }
}

if (-not $jsonOut) {
  $jsonOut = Get-PSSummary $BootstrapDir
}

# Write JSON summary
$jsonOut | Set-Content -Path $SummaryJson -Encoding utf8
Write-Host "• Wrote: $SummaryJson"

# Append CSV
$sum = $jsonOut | ConvertFrom-Json
if (-not (Test-Path $RunsCsv)) {
  "ts,type,ok,tx_log_lines" | Set-Content -Path $RunsCsv -Encoding utf8
}
$line = ('{0},bootstrap,{1},{2}' -f $sum.ts, ($(if ($sum.ok) {'true'} else {'false'})), $sum.counts.tx_log_lines)
Add-Content -Path $RunsCsv -Value $line -Encoding utf8
Write-Host "• Appended: $RunsCsv"

# Also write a human text summary next to artifacts (idempotent)
$human = Join-Path $BootstrapDir "bootstrap_summary_testnet.txt"
$presentKeys = ($sum.present.GetEnumerator() | Where-Object { $_.Value } | ForEach-Object { $_.Key }) -join ", "
@(
  "COLINK XRPL Testnet Bootstrap — summary",
  "UTC: $($sum.ts)",
  "Folder: $($sum.folder)",
  "Present: $presentKeys",
  "tx_log lines: $($sum.counts.tx_log_lines)",
  "OK: $($sum.ok)"
) | Set-Content -Path $human -Encoding utf8
Write-Host "• Wrote: $human"
