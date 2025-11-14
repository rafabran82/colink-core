param(
    [string]$ApiUrl = "http://127.0.0.1:8000"
)

Write-Host "🛡️ Running EWS-MASTER..." -ForegroundColor Cyan

# Track fail state
$Global:FAILED = $false

function Mark-Fail {
    param(
        [string]$Message
    )
    Write-Host "❌ $Message" -ForegroundColor Red
    $Global:FAILED = $true
}

# ---------------------------------------------------------
# 1) Dashboard smoke test
# ---------------------------------------------------------
Write-Host "`n▶ DASHBOARD SMOKE" -ForegroundColor Yellow
try {
    & "$PSScriptRoot\dashboard.smoke.ps1" -ApiUrl $ApiUrl
} catch {
    Mark-Fail "dashboard.smoke.ps1 failed"
}

# ---------------------------------------------------------
# 2) Duplicate-route scan
# ---------------------------------------------------------
Write-Host "`n▶ DUPLICATE ROUTE SCAN" -ForegroundColor Yellow
try {
    $dup = & "$PSScriptRoot\EWS-DUP-SCAN.ps1"
    if ($dup -match "issue group") {
        Mark-Fail "Duplicate routes detected"
    } else {
        Write-Host "   ✅ No duplicate routes"
    }
} catch {
    Mark-Fail "EWS-DUP-SCAN failed"
}

# ---------------------------------------------------------
# 3) Prefix sanity check
# ---------------------------------------------------------
Write-Host "`n▶ PREFIX CHECK" -ForegroundColor Yellow
$main = "colink_core\api\main.py"
if (Test-Path $main) {
    $txt = Get-Content $main -Raw
    if ($txt -match "\\/api" -or $txt -match "'\\\/api'") {
        Mark-Fail "Suspicious escaped prefix found in main.py"
    } else {
        Write-Host "   ✅ Prefixes clean"
    }
} else {
    Mark-Fail "main.py missing?"
}

# ---------------------------------------------------------
# 4) Indentation checker (ignores .venv)
# ---------------------------------------------------------
Write-Host "`n▶ INDENTATION CHECK" -ForegroundColor Yellow

$root    = Get-Location
$pyFiles = Get-ChildItem -Path $root -Recurse -Filter *.py |
           Where-Object { $_.FullName -notlike "*\.venv\*" }

$tabHits = @()

foreach ($f in $pyFiles) {
    try {
        $content = Get-Content -Path $f.FullName -Raw -ErrorAction Stop
        if ($content -match "`t") {
            $tabHits += $f.FullName
        }
    } catch {
        Write-Host "   ℹ️ Skipping unreadable file: $($f.FullName)" -ForegroundColor DarkYellow
    }
}

if ($tabHits.Count -gt 0) {
    Write-Host "   ❌ Tab indentation found in:" -ForegroundColor Red
    $tabHits | Sort-Object -Unique | ForEach-Object {
        Write-Host "      $_"
    }
    Mark-Fail "Tab indentation issues detected"
} else {
    Write-Host "   ✅ Indentation clean" -ForegroundColor Green
}

# ---------------------------------------------------------
# 5) Format checker (Black / isort / etc.)
# ---------------------------------------------------------
Write-Host "`n▶ FORMAT CHECK" -ForegroundColor Yellow
try {
    & "$PSScriptRoot\EWS-FORMAT-CHECK.ps1"
    if ($LASTEXITCODE -ne 0) {
        Mark-Fail "Format check reported issues"
    }
} catch {
    Mark-Fail "Format check failed to execute"
}

# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------
Write-Host "`n======================================" -ForegroundColor DarkGray
if ($Global:FAILED) {
    Write-Host "🔴 EWS-MASTER: FAILURES DETECTED" -ForegroundColor Red
    Write-Host "======================================" -ForegroundColor DarkGray
    exit 1
} else {
    Write-Host "🟢 EWS-MASTER: ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor DarkGray
}
