# --- Phase-20: Build & Test (hardened) ---
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Write-Host "Phase-20: Running tests via python -m pytest -q ..."

# Prefer venv python, then fallback to shim/system
$Root = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (git rev-parse --show-toplevel) }
$Vpy  = Join-Path $Root ".venv\Scripts\python.exe"
$python = $null
if (Test-Path $Vpy) { $python = $Vpy } else { $python = (Get-Command python -ErrorAction SilentlyContinue)?.Source }

if (-not $python) {
  Write-Error "python not found on PATH. Ensure Phase-10 ran and created the venv."
  exit 1
}

# Final sanity: ensure pytest is importable; if not, install it quickly
try {
  & $python - << 'PY'
import importlib, sys
importlib.import_module("pytest")
print("pytest import OK")
PY
} catch {
  Write-Host "pytest not importable in current interpreter — installing pytest..."
  & $python -m pip install pytest
}

# Compose args and run
$pytestArgs = @("-m","pytest","-q")
if ($env:PYTEST_ARGS) { $pytestArgs += $env:PYTEST_ARGS -split '\s+' }

& $python @pytestArgs
$code = $LASTEXITCODE
Write-Host "Phase-20: raw pytest exit code => $code"

# Map code 5 (no tests) to 0 if allowed
$allowNoTests = ($env:ALLOW_PYTEST_NO_TESTS -as [string])
if ($code -eq 5 -and $allowNoTests -and $allowNoTests.ToLower() -in @("1","true","yes")) {
  Write-Host "Phase-20: pytest returned 5 (no tests). ALLOW_PYTEST_NO_TESTS=true -> treating as success."
  exit 0
}

exit $code
