param()
$ErrorActionPreference = "Stop"

# Always call the viewer with -FindRich so we prefer the newest rich schema receipt.
$show = Join-Path $PSScriptRoot "show_last_receipt.ps1"
if (!(Test-Path $show)) { Write-Error "Missing show_last_receipt.ps1 at $show"; exit 1 }

powershell -ExecutionPolicy Bypass -File $show -FindRich
