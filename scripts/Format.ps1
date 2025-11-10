[CmdletBinding()]
param()
$ErrorActionPreference = "Continue"
$venv = ".\.venv\Scripts"
$py   = Join-Path $venv "python.exe"
$ruff = Join-Path $venv "ruff.exe"

Write-Host "==> Ruff (lint + fix, isolated)..."
if (Test-Path $ruff) {
  & $ruff check . --fix --isolated
} elseif (Test-Path $py) {
  & $py -m ruff check . --fix --isolated
} else {
  Write-Host "Ruff not found (ok to skip)"
}

Write-Host "==> Black (format)..."
if (Test-Path $py) {
  & $py -m black .
} else {
  Write-Host "Python venv not found; skipping Black"
}

Write-Host "Format complete."
