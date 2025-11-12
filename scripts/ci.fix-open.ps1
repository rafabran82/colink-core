param(
  [string]$Daily = "scripts\ci.daily.ps1"
)

Write-Host "🔎 Deduping dashboard openers..."

# Patterns that open the dashboard
$psOpenRx = '(?mi)^\s*(Start-Process|Invoke-Item)\s+.*?\.artifacts\\index\.html.*$'
$cmdOpenRx = '(?mi)^\s*(start\b.*?\.artifacts\\index\.html.*|explorer\s+.*?\.artifacts\\index\.html.*)$'

# 1) Disable opens in every PS1/PSM1 except ci.daily.ps1
$psFiles = Get-ChildItem -Recurse -File -Include *.ps1,*.psm1 |
  Where-Object { ($_.FullName -replace '\\','/') -notlike "*scripts/ci.daily.ps1" }

foreach ($f in $psFiles) {
  $orig = Get-Content $f.FullName -Raw
  $txt  = [regex]::Replace($orig, $psOpenRx, '# DISABLED (centralized in ci.daily): $0')
  if ($txt -ne $orig) {
    Set-Content -Path $f.FullName -Encoding utf8 -Value $txt
    Write-Host "🔧 Disabled open in: $($f.FullName)"
  }
}

# 2) Disable opens in all .cmd files and add @echo off
$cmdFiles = Get-ChildItem -Recurse -File -Include *.cmd
foreach ($f in $cmdFiles) {
  $orig = Get-Content $f.FullName -Raw
  $txt  = $orig
  if ($txt -notmatch '^\s*@echo\s+off\s*$') { $txt = "@echo off`r`n" + $txt }
  $txt  = [regex]::Replace($txt, $cmdOpenRx, 'REM DISABLED (centralized in ci.daily): $0')
  if ($txt -ne $orig) {
    [System.IO.File]::WriteAllText($f.FullName, $txt, [System.Text.Encoding]::ASCII)
    Write-Host "🔧 Disabled open in: $($f.FullName)"
  }
}

# 3) Ensure ci.daily.ps1 has exactly ONE open near the end
if (-not (Test-Path $Daily)) { throw "Not found: $Daily" }
$d = Get-Content $Daily -Raw

# Remove ALL existing open lines first
$d = [regex]::Replace($d, $psOpenRx, '')

# Insert single open before the EOF (or after our embed call if present)
$embedLine = '& "`$PSScriptRoot\ci.embed-latest.ps1" -Quiet'
if (-not (Get-Variable -Name "DashboardOpened" -Scope Global -ErrorAction SilentlyContinue)) {
    $Global:DashboardOpened = $true
# DISABLED (centralized in ci.daily):     Start-Process ".artifacts\index.html"
    Write-Host "🌐 Dashboard opened (single instance)."
}

if ($d -match [regex]::Escape($embedLine)) {
  # Place right after embed line (clean separation)
  $d = $d -replace [regex]::Escape($embedLine), ($embedLine + "`r`n" + $openLine)
} else {
  # Append to end
  if ($d -notmatch "`r?`n$") { $d += "`r`n" }
  $d += "`r`n$openLine`r`n"
}

Set-Content -Path $Daily -Encoding utf8 -Value $d
Write-Host "✅ ci.daily.ps1 now owns the single dashboard open."





