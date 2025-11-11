# --- Phase-20: Build & Test (hardened, PS-safe) ---
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Write-Host "Phase-20: Running tests via python -m pytest -q ..."

# Prefer venv python, then fallback to shim/system
$Root = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (git rev-parse --show-toplevel) }
$Vpy  = Join-Path $Root ".venv\Scripts\python.exe"
$python = if (Test-Path $Vpy) { $Vpy } else { (Get-Command python -ErrorAction SilentlyContinue)?.Source }

if (-not $python) {
  Write-Error "python not found on PATH. Ensure Phase-10 ran and created the venv."
  exit 1
}

# Verify pytest import using a temp script (avoids Bash heredoc)
$pyCheck = @"
import importlib
import sys
try:
    importlib.import_module('pytest')
    print('pytest import OK')
except Exception as e:
    sys.exit(99)
"@

$tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "check_pytest_{0}.py" -f ([guid]::NewGuid()))
[IO.File]::WriteAllText($tmp, $pyCheck, [Text.Encoding]::UTF8)

& $python $tmp
$chk = $LASTEXITCODE
Remove-Item -Force $tmp -ErrorAction SilentlyContinue

if ($chk -eq 99) {
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
