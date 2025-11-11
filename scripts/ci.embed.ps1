param(
  [string]$IndexPath = ".artifacts\index.html",
  [string]$ChartRelPath = "ci/runs/runs_trend.png"
)

$ErrorActionPreference = "Stop"
$html = @"
<html><body style='font-family:Segoe UI,sans-serif'>
<h2>Local CI Summary</h2>
<p>Generated: $(Get-Date)</p>
<img src="$ChartRelPath" width="600">
</body></html>
"@
Set-Content -Path $IndexPath -Value $html -Encoding utf8
Write-Host "✅ Embedded trend chart into $IndexPath"
