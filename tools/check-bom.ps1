param()

$bad = @()

Get-ChildItem -Path ".github/workflows" -Include *.yml,*.yaml -Recurse | ForEach-Object {
  $bytes = [IO.File]::ReadAllBytes($_.FullName)
  $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
  # quick CRLF scan
  $content = [Text.Encoding]::UTF8.GetString($bytes)
  $hasCrlf = $content.Contains("`r`n")
  if ($hasBom -or $hasCrlf) { $bad += $_.FullName }
}

if ($bad.Count -gt 0) {
  Write-Error ("BOM/CRLF detected in:`n" + ($bad -join "`n"))
  exit 1
}
