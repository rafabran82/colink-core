param(
  [Parameter(Mandatory=$true)][string]$Path,
  [switch]$Fail
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Directories to skip (regex on full path, both slashes)
$SkipDir = '(?i)(\\|/)(\.venv|\.ruff_cache|\.pytest_cache|build|dist|__pycache__)(\\|/)'

# File extensions to treat as binary and skip
$BinExt = '(?i)\.(png|jpe?g|gif|bmp|tiff?|webp|ico|svgz?|mp4|mov|avi|mkv|webm|mp3|wav|flac|ogg|pdf|zip|7z|gz|tar|tgz|bz2|xz|exe|dll|so|dylib|bin|pyc|pyo|pyd|db|sqlite3?|lock|ttf|otf)$'

# Expand to files
$files = @()
Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
  $p = $_.FullName
  if ($p -match $SkipDir) { return }
  if ($p -match $BinExt)  { return }
  $files += $p
}

if (-not $files -or $files.Count -eq 0) {
  Write-Host "No eligible files to check under: $Path"
  exit 0
}

$violations = @()

foreach ($f in $files) {
  $bytes = [IO.File]::ReadAllBytes($f)
  if ($bytes.Length -eq 0) { continue }

  $hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
  $hasCR  = $false
  foreach ($b in $bytes) { if ($b -eq 0x0D) { $hasCR = $true; break } }

  if ($hasBom -or $hasCR) {
    $violations += [pscustomobject]@{ Path = $f; BOM = $hasBom; CRLF = $hasCR }
  }
}

if ($violations.Count -gt 0) {
  $violations | Sort-Object Path | Format-Table -AutoSize | Out-String | Write-Host
  if ($Fail) { Write-Error "BOM/CRLF detected."; exit 1 } else { Write-Warning "BOM/CRLF detected."; exit 0 }
} else {
  Write-Host "OK: No BOM and LF-only line endings."
  exit 0
}
