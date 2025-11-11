param(
  [string]$RunsLog = ".artifacts\ci\runs\runs_log.csv",
  [int]$Count = 5
)

if (!(Test-Path $RunsLog)) { return "" }
$rows = Get-Content $RunsLog | Select-Object -Last $Count
if (-not $rows) { return "" }

# Build simple HTML table
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("<h3>Last $Count Runs</h3>")
[void]$sb.AppendLine("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;font-family:Segoe UI,sans-serif'>")
[void]$sb.AppendLine("<tr><th>Timestamp</th><th>Files</th><th>Total MB</th></tr>")
$rows | ForEach-Object {
  $parts = $_ -split ','
  if ($parts.Count -ge 3) {
    $ts,$files,$mb = $parts[0],$parts[1],$parts[2]
    [void]$sb.AppendLine("<tr><td>$ts</td><td style='text-align:right'>$files</td><td style='text-align:right'>$mb</td></tr>")
  }
}
[void]$sb.AppendLine("</table>")
$sb.ToString()
