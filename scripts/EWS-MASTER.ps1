Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🔍 EWS-MASTER — Early Warning System" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan

$checks = @(
    "EWS-DUP-SCAN.ps1",
    "EWS-PREFIX-CHECK.ps1",
    "EWS-FIX-INDENT.ps1",
    "EWS-FORMAT-CHECK.ps1",
    "EWS-ROUTE-CHECK.ps1"
)

foreach ($check in $checks) {
    if (Test-Path $check) {
        Write-Host "`n▶ Running $check ..." -ForegroundColor DarkYellow
        & .\$check
    } else {
        Write-Host "❌ Missing script: $check" -ForegroundColor Red
    }
}

Write-Host "`n==============================="
Write-Host "🟢 EWS-MASTER: ALL CHECKS DONE"
Write-Host "==============================="
