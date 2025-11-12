[CmdletBinding()]
param(
  [string]$BootstrapDir = ".artifacts/data/bootstrap",
  [string]$SummaryJson  = ".artifacts/ci/bootstrap.summary.json",
  [string]$RunsCsv      = ".artifacts/ci/runs_log.csv"
)
$ErrorActionPreference = "Stop"

function New-JsonSummary([string]$folder, [hashtable]$present, [int]$txLines, [bool]$ok, [string]$note) {
  [ordered]@{
    ok      = $ok
    ts      = [DateTime]::UtcNow.ToString("o")
    folder  = $folder
    present = $present
    counts  = @{ tx_log_lines = $txLines }
    notes   = @($note)
  } | ConvertTo-Json -Depth 6
}

# Ensure output dirs
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SummaryJson) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RunsCsv)     | Out-Null

# Scan presence
$targets = @(
  "wallets.json","trustlines.json","offers.json","tx_log.ndjson",
  "bootstrap_meta.json","bootstrap_plan_testnet.json",
  "bootstrap_result_testnet.json","bootstrap_summary_testnet.txt"
)
$present = @{}
foreach ($t in $targets) {
  $present[$t] = Test-Path (Join-Path $BootstrapDir $t)
}

# tx_log non-empty line count
$txPath = Join-Path $BootstrapDir "tx_log.ndjson"
$txLines = 0
if (Test-Path $txPath) {
  $lines = Get-Content $txPath -ErrorAction SilentlyContinue
  if ($lines) {
    $txLines = ($lines | Where-Object { $_.Trim() -ne '' } | Measure-Object -Line).Lines
  }
}

$ok = ($present.Values | Where-Object { $_ } | Measure-Object).Count -gt 0
$json = New-JsonSummary -folder $BootstrapDir -present $present -txLines $txLines -ok $ok -note "ps-only verifier"

# Write JSON summary
$json | Set-Content -Path $SummaryJson -Encoding utf8
Write-Host "• Wrote: $SummaryJson"

# Append CSV
if (-not (Test-Path $RunsCsv)) {
  "ts,type,ok,tx_log_lines" | Set-Content -Path $RunsCsv -Encoding utf8
}
$sum = $json | ConvertFrom-Json
$csvLine = ('{0},bootstrap,{1},{2}' -f $sum.ts, ($(if ($sum.ok) {'true'} else {'false'})), $sum.counts.tx_log_lines)
Add-Content -Path $RunsCsv -Value $csvLine -Encoding utf8
Write-Host "• Appended: $RunsCsv → $csvLine"

# Human text summary (beside artifacts)
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
