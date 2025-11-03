param(
  [string]$Root = ".\phase2\xrpl\otc_receipts",
  [string]$Pattern = "otc-*.json"
)

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$files = Get-ChildItem -Path $Root -Filter $Pattern -File -ErrorAction SilentlyContinue
if (-not $files) { Write-Host "No matching files under $Root"; exit 0 }

foreach ($f in $files) {
  try {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
      $text = Get-Content -Raw -Path $f.FullName
      [System.IO.File]::WriteAllText($f.FullName, $text, $utf8NoBom)
      Write-Host "✅ Stripped BOM: $($f.Name)"
    }
  } catch {
    Write-Warning "Skip $($f.FullName): $($_.Exception.Message)"
  }
}
