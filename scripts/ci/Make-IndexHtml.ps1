# Make-IndexHtml.ps1 — PS5-safe artifact index
$ErrorActionPreference = "Stop"

function Format-Size([long]$bytes) {
  if ($bytes -lt 1024) { return "$bytes B" }
  if ($bytes -lt 1MB)  { return ("{0:N0} KB" -f [math]::Ceiling($bytes/1KB)) }
  return ("{0:N1} MB" -f ($bytes/1MB))
}

function HtmlEscape([string]$s) {
  if ($null -eq $s) { return "" }
  $s = $s -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' -replace '"','&quot;'
  return $s
}

# PS5-safe relative path (no Path.GetRelativePath)
function Get-RelPath([string]$baseDir, [string]$targetPath) {
  $base = (Resolve-Path -LiteralPath $baseDir).ProviderPath
  if ($base[-1] -ne '\' -and $base[-1] -ne '/') { $base += '\' }
  $uBase   = New-Object System.Uri($base)
  $uTarget = New-Object System.Uri((Resolve-Path -LiteralPath $targetPath).ProviderPath)
  $rel = $uBase.MakeRelativeUri($uTarget).ToString()
  return [System.Uri]::UnescapeDataString($rel)
}

$root = (Get-Location).Path
$art  = Join-Path $root ".artifacts"

function New-LinkRow([System.IO.FileSystemInfo]$File) {
  if (-not $File -or -not (Test-Path -LiteralPath $File.FullName)) { return "" }
  $name = HtmlEscape $File.Name
  $rel  = Get-RelPath $art $File.FullName
  $len  = if ($File -is [System.IO.FileInfo]) { $File.Length } else { 0 }
  $size = if ($len -gt 0) { " <span>($(Format-Size $len))</span>" } else { "" }
  return "<li><a href=""$rel"">$name</a>$size</li>"
}

function List-Section([string]$Title, [string]$Dir, [string]$Filter = "*") {
  if (-not (Test-Path -LiteralPath $Dir)) { return "" }
  $files = Get-ChildItem -LiteralPath $Dir -File -Filter $Filter -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -ne ".gitkeep" } |
           Sort-Object Name
  if (-not $files) { return "" }
  $lis = ($files | ForEach-Object { New-LinkRow $_ }) -join "`n"
  $titleEsc = HtmlEscape $Title
  return "<h2>$titleEsc</h2><ul>$lis</ul>"
}

function Build-Badge() {
  $badgePath = Join-Path $art "ci\ci_badge.json"
  if (-not (Test-Path -LiteralPath $badgePath)) { return "" }
  try {
    $obj = Get-Content -Raw -LiteralPath $badgePath | ConvertFrom-Json
    $color = switch ($obj.color) {
      "green"  { "#16a34a" } "red" { "#dc2626" } "yellow" { "#ca8a04" } default { "#6b7280" }
    }
    $label = ("" + $obj.status).ToUpper()
    $text = ""
    if ($obj.passed -ne $null -and $obj.failed -ne $null -and $obj.skipped -ne $null) {
      $total = [int]$obj.passed + [int]$obj.failed + [int]$obj.skipped
      $text = "$total — $($obj.passed) passed; skipped $($obj.skipped); failed $($obj.failed)"
    }
    if ($obj.time_total_sec -ne $null) {
      $text += ("; time {0:N3}s" -f [double]$obj.time_total_sec)
    }
    $textEsc = HtmlEscape $text
    return "<div class=""badge""><span class=""dot"" style=""background:$color""></span><strong>$label</strong> — $textEsc</div>"
  } catch { return "" }
}

$badgeHtml   = Build-Badge
$ciHtml      = List-Section "CI files"   (Join-Path $art "ci")
$plotsHtml   = List-Section "Plots"      (Join-Path $art "plots")   "*.png"
$metricsHtml = List-Section "Metrics"    (Join-Path $art "metrics") "*.ndjson"
$bundlesHtml = List-Section "Bundles"    (Join-Path $art "bundles") "*.zip"

$html = @"
<!doctype html>
<meta charset="utf-8">
<title>Artifacts</title>
<style>
  body{font:16px system-ui,Segoe UI,Arial,sans-serif;margin:24px;line-height:1.45}
  h1{font-size:32px;margin:0 0 8px}
  .badge{margin:10px 0 16px;padding:8px 12px;background:#f6f8fa;border:1px solid #e5e7eb;border-radius:10px;display:inline-block}
  .dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}
  ul{margin:6px 0 18px 20px} li span{color:#6b7280;margin-left:6px}
  h2{font-size:18px;margin:16px 0 6px}
</style>
<h1>Artifacts</h1>
$badgeHtml
$ciHtml
$plotsHtml
$metricsHtml
$bundlesHtml
"@

New-Item -ItemType Directory -Force -Path $art | Out-Null
Set-Content -LiteralPath (Join-Path $art "index.html") -Encoding utf8 -Value $html
Write-Host "index.html written to $art"
