param(
    [string]$ApiUrl = "http://127.0.0.1:8000"
)

Write-Host "🛡️ Running EWS-MASTER..." -ForegroundColor Cyan

# Track fail state
$Global:FAILED = $false

function Mark-Fail($msg) {
    Write-Host "❌ $msg" -ForegroundColor Red
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
# 4) Indentation checker (basic, ignores .venv)
# ---------------------------------------------------------
Write-Host "`n▶ INDENTATION CHECK" -ForegroundColor Yellow

$pyFiles = Get-ChildItem -Recurse -Filter *.py | Where-Object {
    param(
    [string]$ApiUrl = "http://127.0.0.1:8000"
)

Write-Host "🛡️ Running EWS-MASTER..." -ForegroundColor Cyan

# Track fail state
$Global:FAILED = $false

function Mark-Fail($msg) {
    Write-Host "❌ $msg" -ForegroundColor Red
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
# 4) Indentation checker (basic)
# ---------------------------------------------------------
Write-Host "`n▶ INDENTATION CHECK" -ForegroundColor Yellow
$pyFiles = Get-ChildItem -Recurse -Filter *.py
foreach ($f in $pyFiles) {
    $raw = Get-Content $f.FullName
    foreach ($line in $raw) {
        if ($line -match "`t") {
            Mark-Fail "Tab indentation detected in $($f.FullName)"
            break
        }
    }
}
if (-not $Global:FAILED) {
    Write-Host "   ✅ Indentation clean"
}

# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------
Write-Host "`n======================================" -ForegroundColor DarkGray
if ($Global:FAILED) {
    Write-Host "🔴 EWS-MASTER: FAILURES DETECTED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "🟢 EWS-MASTER: ALL CHECKS PASSED" -ForegroundColor Green
}
======================================
.FullName -notmatch "\\.venv\\"
}

foreach ($f in $pyFiles) {
    $raw = Get-Content $f.FullName
    foreach ($line in $raw) {
        if ($line -match "`t") {
            Mark-Fail "Tab indentation detected in $($f.FullName)"
            break
        }
    }
}

if (-not $Global:FAILED) {
    Write-Host "   ✅ Indentation clean"
}

# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------
Write-Host "`n======================================" -ForegroundColor DarkGray
if ($Global:FAILED) {
    Write-Host "🔴 EWS-MASTER: FAILURES DETECTED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "🟢 EWS-MASTER: ALL CHECKS PASSED" -ForegroundColor Green
}
======================================


