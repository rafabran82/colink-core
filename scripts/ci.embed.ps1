param(
  [Parameter(Mandatory)][string]$IndexPath,
  [Parameter(Mandatory)][string]$ChartRelPath,
  [string]$ExtraHtml = "",
  [string]$FooterHtml = ""
)

$now = Get-Date
$html = @"
<html>
  <body style='font-family:Segoe UI,sans-serif'>
    <h1>Local CI Summary</h1>
    <p>Generated: $now</p>
    <h3>Local CI Run Trend</h3>
    <img src="$ChartRelPath" width="600" />
    <div style='margin-top:18px'>$ExtraHtml</div>
    <div>$FooterHtml</div>
  </body>
</html>
"@
Set-Content -Path $IndexPath -Value $html -Encoding utf8
Write-Host "✅ Embedded trend chart into $IndexPath"
