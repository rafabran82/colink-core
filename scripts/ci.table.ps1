param(
  [string]$RunsLog = ".artifacts\ci\runs\runs_log.csv",
  [int]$Count = 5,
  [string]$TimeZone = 'Local'
)

$pat = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d+,\d+(\.\d+)?$'
if (!(Test-Path $RunsLog)) { return "" }

. "$PSScriptRoot\ci.tz.ps1"

$rows = Get-Content $RunsLog | Where-Object { $_ -match $pat }
$validCount = ($rows | Measure-Object).Count
$rows = $rows | Select-Object -Last $Count

$sb = New-Object System.Text.StringBuilder
$tzLabel = $TimeZone
[void]$sb.AppendLine("<h3>Last $Count Runs <span style='font-size:12px;color:#555'>(TZ: $tzLabel, valid rows: $validCount)</span></h3>")
[void]$sb.AppendLine("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;font-family:Segoe UI,sans-serif'>")
[void]$sb.AppendLine("<tr><th>Timestamp</th><th>Files</th><th>Total MB</th></tr>")

foreach ($r in $rows) {
  $parts = $r -split ',',3
  if ($parts.Count -ge 3) {
    $ts,$files,$mb = $parts[0],$parts[1],$parts[2]
    $tsDisp = if ($TimeZone -and $TimeZone -ne 'Local') { Convert-IsoToZone $ts $TimeZone } else { $ts }
    [void]$sb.AppendLine("<tr><td>$tsDisp</td><td style='text-align:right'>$files</td><td style='text-align:right'>$mb</td></tr>")
  }
}
[void]$sb.AppendLine("</table>")
$sb.ToString()



