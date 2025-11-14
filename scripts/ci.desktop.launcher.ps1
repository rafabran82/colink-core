# COLINK Guarded CI desktop launcher
# This is the entrypoint your Desktop shortcut will call.

Set-Location "C:\Users\sk8br\Desktop\colink-core"

Write-Host "Launching COLINK Guarded CI from desktop shortcut..." -ForegroundColor Cyan
Write-Host ""

pwsh -NoLogo -NoExit -File "scripts\ci.guard-all.ps1"
