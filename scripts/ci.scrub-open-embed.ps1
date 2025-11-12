param(
  [string]$Daily = "scripts\ci.daily.ps1"
)

Write-Host "🔎 Scrubbing duplicate dashboard opens & embed calls..."

# --- Regexes ---
$rxOpenPs  = '(?mi)^\s*(Start-Process|Invoke-Item)\s+.*?\.artifacts\\index\.html.*$'
$rxOpenCmd = '(?mi)^\s*(start\b.*?\.artifacts\\index\.html.*|explorer\s+.*?\.artifacts\\index\.html.*)$'
$rxEmbedPs = '(?mi)^\s*&.*ci\.embed-latest\.ps1.*$'
$rxEmbedSh = '(?mi)^\s*(pwsh|powershell)\b.*ci\.embed-latest\.ps1.*$'

# 1) Disable opens/embeds in all PS scripts except ci.daily.ps1
Get-ChildItem -Recurse -File -Include *.ps1,*.psm1 |
  Where-Object { ($_.FullName -replace '\\','/') -notlike "*scripts/ci.daily.ps1" } |
  ForEach-Object {
    $orig = Get-Content $_.FullName -Raw
    $txt  = $orig
    $txt  = [regex]::Replace($txt, $rxOpenPs,  '# DISABLED (centralized in ci.daily open): $0')
    $txt  = [regex]::Replace($txt, $rxEmbedPs, '# DISABLED (centralized in ci.daily embed): $0')
    $txt  = [regex]::Replace($txt, $rxEmbedSh, '# DISABLED (centralized in ci.daily embed): $0')
    if ($txt -ne $orig) {
      Set-Content -Path $_.FullName -Encoding utf8 -Value $txt
      Write-Host "🔧 Patched: $($_.FullName)"
    }
  }

# 2) Disable opens/embeds in all .cmd files, add @echo off
Get-ChildItem -Recurse -File -Include *.cmd |
  ForEach-Object {
    $orig = Get-Content $_.FullName -Raw
    $txt  = $orig
    if ($txt -notmatch '^\s*@echo\s+off\s*$') { $txt = "@echo off`r`n" + $txt }
    $txt  = [regex]::Replace($txt, $rxOpenCmd, 'REM DISABLED (centralized in ci.daily open): $0')
    $txt  = [regex]::Replace($txt, '(?mi)^\s*(pwsh|powershell)\b.*ci\.embed-latest\.ps1.*$', 'REM DISABLED (centralized in ci.daily embed): $0')
    $txt  = [regex]::Replace($txt, '(?mi)^\s*echo\s+Write-Host\s+.*$', 'REM (was echo Write-Host ...)')
    if ($txt -ne $orig) {
      [System.IO.File]::WriteAllText($_.FullName, $txt, [System.Text.Encoding]::ASCII)
      Write-Host "🔧 Patched: $($_.FullName)"
    }
  }

# 3) Ensure ci.daily.ps1 has single embed then single open (absolute path), near the end
if (-not (Test-Path $Daily)) { throw "Not found: $Daily" }
$d = Get-Content $Daily -Raw

# Remove any existing embed/open lines first (fresh slate)
$d = [regex]::Replace($d, $rxEmbedPs, '')
$d = [regex]::Replace($d, $rxEmbedSh, '')
$d = [regex]::Replace($d, $rxOpenPs,  '')

$embedLine = '& "`$PSScriptRoot\ci.embed-latest.ps1" -Quiet'
$openBlock = @"
# --- Open dashboard once (absolute path from repo root) ---
`$repoRoot = Split-Path `$PSScriptRoot -Parent
`$index    = Join-Path `$repoRoot ".artifacts\index.html"
if (Test-Path `$index) {
  Start-Process `$index
  Write-Host "🌐 Dashboard opened: `$index"
} else {
  Write-Warning "Dashboard not found: `$index"
}
"@.Trim()

# Insert both right at the tail: after delta summary section is typically written
if ($d -notmatch "`r?`n$") { $d += "`r`n" }
$d += "`r`n$embedLine`r`n$openBlock`r`n"

Set-Content -Path $Daily -Encoding utf8 -Value $d
Write-Host "✅ Centralized single embed + single open in $Daily"
