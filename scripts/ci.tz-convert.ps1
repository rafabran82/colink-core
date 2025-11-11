param(
  [Parameter(Mandatory)][string]$InCsv,
  [Parameter(Mandatory)][string]$OutCsv,
  [string]$TimeZone = 'Local'
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\ci.tz.ps1"

if (!(Test-Path $InCsv)) { throw "Input CSV not found: $InCsv" }
$pat = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d+,\d+(\.\d+)?$'
$lines = Get-Content $InCsv | Where-Object { $_ -match $pat }

$tz = $TimeZone
$fmt = [Globalization.CultureInfo]::InvariantCulture
$out = foreach ($l in $lines) {
  $ts,$files,$mb = $l.Split(',',3)
  $ts2 = Convert-IsoToZone -Iso $ts -Target $tz
  '{0},{1},{2}' -f $ts2, $files, ([double]$mb).ToString('0.###', $fmt)
}
Set-Content $OutCsv -Value $out -Encoding utf8
Write-Host "🕒 Wrote TZ-converted CSV ($TimeZone): $OutCsv  (rows=$($out.Count))"
