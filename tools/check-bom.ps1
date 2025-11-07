$ErrorActionPreference = "Stop"

$badBom = @()
$badCrlf = @()

Get-ChildItem . -File -Include *.yml,*.yaml -Recurse | ForEach-Object {
  $p = $_.FullName

  # --- BOM check (239 187 191) ---
  $b = [IO.File]::ReadAllBytes($p)
  if ($b.Length -ge 3 -and $b[0]-eq 239 -and $b[1]-eq 187 -and $b[2]-eq 191) {
    $badBom += $p
  }

  # --- CRLF check ---
  # scan raw bytes for 0x0D 0x0A
  for ($i=0; $i -lt ($b.Length-1); $i++) {
    if ($b[$i] -eq 13 -and $b[$i+1] -eq 10) { $badCrlf += $p; break }
  }
}

if ($badBom.Count -gt 0) {
  Write-Error ("BOM detected in:`n" + ($badBom -join "`n"))
  exit 1
}

if ($badCrlf.Count -gt 0) {
  Write-Error ("CRLF detected (expected LF) in:`n" + ($badCrlf -join "`n"))
  exit 1
}

Write-Host "OK: No BOM and no CRLF in workflow YAMLs." -ForegroundColor Green
