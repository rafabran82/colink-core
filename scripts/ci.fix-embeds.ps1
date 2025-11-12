param(
  [string]$DailyPath = "scripts\ci.daily.ps1",
  [string]$RunsIndex = ".artifacts\index.html"
)

Write-Host "🔎 Scanning for duplicate embed callers..."

# Collect all ps1/psm1/cmd files
$all = Get-ChildItem -Recurse -File -Include *.ps1,*.psm1,*.cmd

# Patterns that might invoke the embed script
$rxDirect   = '(?mi)^\s*&.*ci\.embed-latest\.ps1.*$'
$rxPwshLine = '(?mi)^\s*(pwsh|powershell)\b.*ci\.embed-latest\.ps1.*$'

# 1) Disable every caller except ci.daily.ps1
$patched = @()
foreach ($f in $all) {
  $isDaily = ($f.FullName -replace '\\','/') -like "*scripts/ci.daily.ps1"
  $txt = Get-Content $f.FullName -Raw

  if ($isDaily) {
    # Strip any existing embed calls; we'll reinsert a single quiet call later
    $t2 = [regex]::Replace($txt, $rxDirect, '')
    $t2 = [regex]::Replace($t2, $rxPwshLine, '')
    if ($t2 -ne $txt) {
      Set-Content -Path $f.FullName -Encoding utf8 -Value $t2
      $patched += $f.FullName
    }
    continue
  }

  # For non-daily files: comment out any embed invocation
  $orig = $txt
  $txt  = [regex]::Replace($txt, $rxDirect,  '# DISABLED (centralized in ci.daily): $0')
  $txt  = [regex]::Replace($txt, $rxPwshLine,'# DISABLED (centralized in ci.daily): $0')

  if ($f.Extension -ieq ".cmd") {
    if ($txt -notmatch '^\s*@echo\s+off\s*$') { $txt = "@echo off`r`n" + $txt }
    # Also silence any 'echo Write-Host ...'
    $txt = [regex]::Replace($txt, '(?mi)^\s*echo\s+Write-Host\s+.*$', 'REM (was echo Write-Host ...)')
    # Save .cmd in ANSI/ASCII
    if ($txt -ne $orig) {
      [System.IO.File]::WriteAllText($f.FullName, $txt, [System.Text.Encoding]::ASCII)
      $patched += $f.FullName
    }
  } else {
    if ($txt -ne $orig) {
      Set-Content -Path $f.FullName -Encoding utf8 -Value $txt
      $patched += $f.FullName
    }
  }
}

# 2) Reinsert a single quiet call in ci.daily.ps1 BEFORE the dashboard open (or append)
if (-not (Test-Path $DailyPath)) { throw "Not found: $DailyPath" }
$d = Get-Content $DailyPath -Raw

# Ensure we have no lingering embed calls
$d = [regex]::Replace($d, $rxDirect, '')
$d = [regex]::Replace($d, $rxPwshLine, '')

$embedLine   = "& `"`$PSScriptRoot\ci.embed-latest.ps1`" -Quiet"
$openPattern = '(?m)^\s*(Start-Process|Invoke-Item)\s+.*?\.artifacts\\index\.html.*$'

if ([regex]::IsMatch($d, $openPattern)) {
  $d = [regex]::Replace($d, $openPattern, "$embedLine`r`n$0", 1)
} else {
  if ($d -notmatch "`r?`n$") { $d += "`r`n" }
  $d += "`r`n$embedLine`r`n"
}

Set-Content -Path $DailyPath -Encoding utf8 -Value $d
$patched += $DailyPath

# 3) Summary + exit code
$patched = $patched | Sort-Object -Unique
if ($patched.Count -gt 0) {
  Write-Host "✅ Patched:" -ForegroundColor Green
  $patched | ForEach-Object { Write-Host "  - $_" }
  exit 0
} else {
  Write-Host "ℹ️ No changes were necessary."
  exit 0
}
