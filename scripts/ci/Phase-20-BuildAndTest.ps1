# --- Phase-20: Build & Test (hardened) ---
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Write-Host "Phase-20: Running tests via python -m pytest -q ..."
# Resolve python explicitly (actions/setup-python guarantees it)
$python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $python) {
  Write-Error "python not found on PATH. Ensure actions/setup-python ran."
  exit 1
}

# Compose args
$pytestArgs = @("-m","pytest","-q")
if ($env:PYTEST_ARGS) { $pytestArgs += $env:PYTEST_ARGS -split '\s+' }

# Execute
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
