param(
  [string]$Root = ".",
  [string]$Pattern = "*.json",
  [switch]$Recurse,
  [switch]$Quiet
)

function Say([string]$msg) { if (-not $Quiet) { Write-Host $msg } }

$searchParams = @{
  Path        = $Root
  Filter      = $Pattern
  File        = $true
  ErrorAction = "SilentlyContinue"
}
if ($Recurse) { $searchParams["Recurse"] = $true }

$files = Get-ChildItem @searchParams
if (-not $files -or $files.Count -eq 0) {
  Say "No matching files under $Root (pattern: $Pattern)."
  exit 0
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

[int]$changed = 0
foreach ($f in $files) {
  try {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
      $text = Get-Content -Raw -Path $f.FullName
      [System.IO.File]::WriteAllText($f.FullName, $text, $utf8NoBom)
      $changed++
      if (-not $Quiet) { Write-Host "✅ Stripped BOM: $($f.FullName)" }
    } else {
      if (-not $Quiet) { Write-Host "OK (no BOM): $($f.FullName)" }
    }
  } catch {
    Write-Warning "Skip $($f.FullName): $($_.Exception.Message)"
  }
}

if (-not $Quiet) {
  Write-Host "Done. Files modified: $changed / $($files.Count)."
}
