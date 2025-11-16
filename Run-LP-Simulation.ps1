param(
    [int]$TopN = 20,
    [switch]$TestMode
)
# --- Load dashboard module ---
. "$PSScriptRoot\scripts\Show-LP-Dashboard.ps1"

Write-Host "=== LAYER 1 OK ===" -ForegroundColor Green
Write-Host "TopN: $TopN" -ForegroundColor Cyan
Write-Host "TestMode: $TestMode" -ForegroundColor Cyan

return 0

