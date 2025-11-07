# Fail on BOM at start of file and on any CR characters in workflow YAMLs.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

$targets = Get-ChildItem -Path (Join-Path $root ".github/workflows") -File -Recurse -Include *.yml,*.yaml

$badBom  = @()
$badCRLF = @()

foreach ($f in $targets) {
  $bytes = [IO.File]::ReadAllBytes($f.FullName)
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $badBom += $f.FullName
  }

  # Read as raw text without rewriting newlines
  $raw = [System.Text.Encoding]::UTF8.GetString($bytes)
  if ($raw -match "`r") { $badCRLF += $f.FullName }
}

if ($badBom.Count -gt 0) {
  Write-Error ("BOM detected in:`n" + ($badBom -join "`n"))
  exit 1
}
if ($badCRLF.Count -gt 0) {
  Write-Error ("CR/CRLF detected in:`n" + ($badCRLF -join "`n"))
  exit 1
}

Write-Output "OK: workflows are UTF-8 (no BOM) + LF-only"
exit 0