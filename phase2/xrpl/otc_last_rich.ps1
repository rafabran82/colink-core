param()
$p = Join-Path $PSScriptRoot "show_last_receipt.ps1"
if (!(Test-Path $p)) { Write-Error "Missing show_last_receipt.ps1"; exit 1 }
powershell -ExecutionPolicy Bypass -File $p -FindRich
