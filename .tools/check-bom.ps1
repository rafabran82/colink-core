param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$Path,
  [switch]$Fail
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Expand globs to files
$files = @()
Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $files += $_.FullName }
if ($files.Count -eq 0) {
  Write-Host "No files matched: $Path"
  exit 0
}

$violations = @()

foreach ($f in $files) {
  $bytes = [IO.File]::ReadAllBytes($f)
  if ($bytes.Length -eq 0) { continue }

  # UTF-8 BOM?
  $hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF

  # Any CR bytes?
  $hasCR = $false
  foreach ($b in $bytes) {
    if ($b -eq 0x0D) { $hasCR = $true; break }
  }

  if ($hasBom -or $hasCR) {
    $violations += [pscustomobject]@{
      Path = $f
      BOM  = $hasBom
      CRLF = $hasCR
    }
  }
}

if ($violations.Count -gt 0) {
  $violations | Sort-Object Path | Format-Table -AutoSize | Out-String | Write-Host
  if ($Fail) {
    Write-Error "BOM/CRLF detected."
    exit 1
  } else {
    Write-Warning "BOM/CRLF detected."
    exit 0
  }
} else {
  Write-Host "OK: No BOM and LF-only line endings."
  exit 0
}
