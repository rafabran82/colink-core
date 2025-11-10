# --- Phase-10: Bootstrap venv + deps (idempotent) ---
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Write-Host "== Phase-10: Bootstrap venv + deps =="

# Resolve workspace and venv paths
$Root = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (git rev-parse --show-toplevel) }
$Venv = Join-Path $Root ".venv"
$PyExe = $null

# Prefer the setup-python shim first, then system python
$PyExe = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $PyExe) { throw "python not found on PATH (actions/setup-python should run before Phase-10)." }

# Create venv if missing
if (-not (Test-Path $Venv)) {
  Write-Host "Creating venv at $Venv"
  & $PyExe -m venv $Venv
}

$Vpy = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $Vpy)) { throw "Venv python not found at $Vpy" }

# Upgrade build tooling
& $Vpy -m pip install --upgrade pip setuptools wheel

# Install dev/test deps
$reqDev = Join-Path $Root "requirements-dev.txt"
$reqTxt = Join-Path $Root "requirements.txt"

if (Test-Path $reqDev) {
  Write-Host "Installing dev requirements: $reqDev"
  & $Vpy -m pip install -r $reqDev
} else {
  Write-Host "No requirements-dev.txt found; installing minimal dev toolchain."
  & $Vpy -m pip install pytest
}

# Optionally install runtime requirements (skip if you prefer split deps)
if (Test-Path $reqTxt) {
  Write-Host "Installing runtime requirements: $reqTxt"
  & $Vpy -m pip install -r $reqTxt
}

# Expose venv to subsequent steps
# - Add venv Scripts to PATH
# - Set VIRTUAL_ENV for downstream scripts
if ($env:GITHUB_PATH) {
  (Join-Path $Venv "Scripts") | Out-File -FilePath $env:GITHUB_PATH -Encoding utf8 -Append
}
if ($env:GITHUB_ENV) {
  "VIRTUAL_ENV=$Venv" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
}

Write-Host "Bootstrap complete. Venv: $Venv"
