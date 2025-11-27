Param(
  [Parameter(Position=0)][string]$Path = ".",
  [switch]$Fail
)

# Text-only whitelist (avoid binaries)
$exts = @(
  ".ps1",".psm1",".psd1",
  ".py",".toml",".md",".txt",".json",".yaml",".yml",
  ".tf",".tfvars",".ini",".cfg",".conf",".sh",".bat",".cmd"
)

# Exclude common junk/caches & VCS
$exclude = [regex]"\\(\.git|\.venv|\.ruff_cache|\.pytest_cache|node_modules|dist|build)(\\|$)"

$results = New-Object System.Collections.Generic.List[Object]

Get-ChildItem -Path $Path -Recurse -File -Force |
  Where-Object {
    $_.FullName -notmatch $exclude -and $exts -contains $_.Extension.ToLower()
  } |
  ForEach-Object {
    $p = $_.FullName
    $bytes = [IO.File]::ReadAllBytes($p)

    # UTF-8 BOM?
    $hasBom = $false
    if ($bytes.Length -ge 3) {
      $hasBom = ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    }

    # CRLF check using raw bytes (0x0D 0x0A sequence)
    $hasCrlf = $false
    for ($i=0; $i -lt $bytes.Length-1; $i++) {
      if ($bytes[$i] -eq 0x0D -and $bytes[$i+1] -eq 0x0A) { $hasCrlf = $true; break }
    }

    $results.Add([PSCustomObject]@{
      Path = $p
      BOM  = $hasBom
      CRLF = $hasCrlf
    })
  }

$results | Sort-Object Path | Format-Table -AutoSize

if ($Fail -and ($results | Where-Object { $_.BOM -or $_.CRLF })) {
  Write-Error "BOM/CRLF detected."
  exit 1
}

