[CmdletBinding()]
param(
  [string]$BootstrapDir = ".artifacts/data/bootstrap",
  [string]$SummaryJson  = ".artifacts/ci/bootstrap.summary.json",
  [string]$RunsCsv      = ".artifacts/ci/runs_log.csv"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SummaryJson) | Out-Null
Write-Host "• Running bootstrap verifier…"
$temp = New-TemporaryFile
python "scripts/xrpl.bootstrap.verify.py" "$BootstrapDir" *> $temp.FullName
Get-Content $temp.FullName | Where-Object { $_ -match "🔎 Verifying" } | ForEach-Object { Write-Host $_ }
$raw = Get-Content $temp.FullName -Raw
Remove-Item $temp -Force
$start = $raw.LastIndexOf('{'); $end = $raw.LastIndexOf('}')
if ($start -lt 0 -or $end -lt $start) { throw "Verifier did not emit JSON." }
$json = $raw.Substring($start, $end - $start + 1)
$json | Set-Content -Path $SummaryJson -Encoding utf8
Write-Host "• Wrote: $SummaryJson"
$sum = $json | ConvertFrom-Json
if (-not (Test-Path $RunsCsv)) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RunsCsv) | Out-Null
  "ts,type,ok,tx_log_lines" | Set-Content -Path $RunsCsv -Encoding utf8
}
$line = ('{0},bootstrap,{1},{2}' -f $sum.ts, ($(if ($sum.ok) {'true'} else {'false'})), $sum.counts.tx_log_lines)
Add-Content -Path $RunsCsv -Value $line -Encoding utf8
Write-Host "• Appended: $RunsCsv"
