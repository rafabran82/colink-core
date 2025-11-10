param()
$ErrorActionPreference = "Stop"

Write-Host "== Make-IndexHtml: .artifacts/index.html ==" -ForegroundColor Cyan

$art = Join-Path $PWD ".artifacts"
if (-not (Test-Path $art)) { New-Item -ItemType Directory -Force -Path $art | Out-Null }

function Get-Sha256Hex([string]$Path) {
  $s = [System.Security.Cryptography.SHA256]::Create()
  $fs = [System.IO.File]::OpenRead($Path)
  try {
    $hash = $s.ComputeHash($fs)
    ($hash | ForEach-Object { $_.ToString("x2") }) -join ""
  } finally { $fs.Dispose(); $s.Dispose() }
}

$rows = @()
Get-ChildItem -Path $art -File -Recurse | ForEach-Object {
  $rel = $_.FullName.Substring($art.Length).TrimStart('\','/')
  $sha = Get-Sha256Hex $_.FullName
  $rows += @{
    name = $rel
    size = $_.Length
    sha256 = $sha
  }
}

$tbody = ($rows | ForEach-Object {
  "<tr><td><a href=""$($_.name)"">$($_.name)</a></td><td style='text-align:right'>$($_.size)</td><td><code>$($_.sha256)</code></td></tr>"
}) -join "`n"

$html = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Artifacts Index</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:24px}
  h1{margin-top:0}
  table{border-collapse:collapse;width:100%}
  th,td{border:1px solid #ddd;padding:8px}
  th{background:#f6f8fa;text-align:left}
  code{font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace}
</style>
</head>
<body>
<h1>.artifacts index</h1>
<p>Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
<table>
  <thead><tr><th>File</th><th style="text-align:right">Size (bytes)</th><th>SHA256</th></tr></thead>
  <tbody>
$tbody
  </tbody>
</table>
</body>
</html>
"@

Set-Content -Path (Join-Path $art "index.html") -Value $html -Encoding utf8
Write-Host "Wrote .artifacts/index.html" -ForegroundColor Green
