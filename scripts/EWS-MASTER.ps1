Write-Host "======================================" -ForegroundColor Cyan
Write-Host "ðŸ” EWS-MASTER â€” Early Warning System" -ForegroundColor Yellow
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
        Write-Host "`nâ–¶ Running $check ..." -ForegroundColor DarkYellow
        & .\$check
    } else {
        Write-Host "âŒ Missing script: $check" -ForegroundColor Red
    }
}

Write-Host "`n==============================="
Write-Host "ðŸŸ¢ EWS-MASTER: ALL CHECKS DONE"
Write-Host "==============================="

