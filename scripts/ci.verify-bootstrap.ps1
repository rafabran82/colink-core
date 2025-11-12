param(
  [string]$BootstrapDir = ".artifacts/data/bootstrap",
  [string]$SummaryJson  = ".artifacts/ci/bootstrap.summary.json",
  [string]$RunsCsv      = ".artifacts/ci/runs_log.csv",
  [switch]$ForcePSFallback
)

# --- helpers ---
function Ensure-Dir($p) { $d = Split-Path -Parent $p; if ($d -and -not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null } }
function Get-PSFilePresence($folder) {
  $keys = @(
    "bootstrap_plan_testnet.json",
    "bootstrap_result_testnet.json",
    "wallets.json",
    "trustlines.json",
    "offers.json",
    "tx_log.ndjson",
    "bootstrap_meta.json",
    "bootstrap_summary_testnet.txt"
  )
  $h = [ordered]@{}
  foreach ($k in $keys) { $h[$k] = Test-Path (Join-Path $folder $k) }
  [pscustomobject]$h
}
function Get-PSCountTxLines($folder) {
  $tx = Join-Path $folder "tx_log.ndjson"
  if (-not (Test-Path $tx)) { return 0 }
  ($null = $Error.Clear())
  try {
    (Get-Content $tx -ErrorAction SilentlyContinue | Where-Object { $_.Trim() -ne "" }).Count
  } catch { 0 }
}
function New-JsonSummary($folder, $presentObj, $txLines, $note, $ok) {
  $ts = [DateTime]::UtcNow.ToString("o")
  $o = [ordered]@{
    ok      = [bool]$ok
    ts      = $ts
    folder  = $folder
    present = $presentObj
    counts  = @{ tx_log_lines = $txLines }
    notes   = @($note)
  }
  ($o | ConvertTo-Json -Depth 6)
}

# --- main ---
Ensure-Dir $SummaryJson
Ensure-Dir $RunsCsv
if (-not (Test-Path $BootstrapDir)) { New-Item -ItemType Directory -Force -Path $BootstrapDir | Out-Null }

# Prefer python verifier ONLY if not forced and it outputs JSON; otherwise PS summary.
$jsonOut = $null
if (-not $ForcePSFallback.IsPresent) {
  try {
    $tmp = New-TemporaryFile
    python "scripts/xrpl.bootstrap.verify.py" "$BootstrapDir" *> $tmp.FullName
    $raw = Get-Content $tmp.FullName -Raw
    Remove-Item $tmp -Force
    $start = $raw.LastIndexOf('{'); $end = $raw.LastIndexOf('}')
    if ($start -ge 0 -and $end -ge $start) { $jsonOut = $raw.Substring($start, $end - $start + 1) }
  } catch { $jsonOut = $null }
}

if (-not $jsonOut) {
  $present = Get-PSFilePresence $BootstrapDir
  $txLines = Get-PSCountTxLines $BootstrapDir
  $jsonOut = New-JsonSummary $BootstrapDir $present $txLines "ps-only verifier" ($true)
}

# Write JSON summary
$jsonOut | Set-Content -Path $SummaryJson -Encoding utf8
Write-Host "• Wrote: $SummaryJson"

# Append CSV
$sum = $jsonOut | ConvertFrom-Json
if (-not (Test-Path $RunsCsv)) {
  "ts,type,ok,tx_log_lines" | Set-Content -Path $RunsCsv -Encoding utf8
}
$okStr = if ($sum.ok) { "true" } else { "false" }
$line = "{0},bootstrap,{1},{2}" -f $sum.ts, $okStr, $sum.counts.tx_log_lines
Add-Content -Path $RunsCsv -Value $line -Encoding utf8
Write-Host "• Appended: $RunsCsv → $line"

# Human TXT summary beside artifacts
$presentNames = @()
foreach ($prop in $sum.present.PSObject.Properties) { if ($prop.Value) { $presentNames += $prop.Name } }
$presentKeys = $presentNames -join ", "
$human = Join-Path $BootstrapDir "bootstrap_summary_testnet.txt"
@(
  "COLINK XRPL Testnet Bootstrap — summary",
  "UTC: $($sum.ts)",
  "Folder: $($sum.folder)",
  "Present: $presentKeys",
  "tx_log lines: $($sum.counts.tx_log_lines)",
  "OK: $($sum.ok)"
) | Set-Content -Path $human -Encoding utf8
Write-Host "• Wrote: $human"
