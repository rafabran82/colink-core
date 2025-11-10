param()
$ErrorActionPreference = "Stop"

Write-Host "== Phase-10: Bootstrap venv + deps ==" -ForegroundColor Cyan

# Use .venv at repo root
$venv = Join-Path $PWD ".venv"
if (-not (Test-Path $venv)) {
  Write-Host "Creating venv at $venv"
  python -m venv $venv
}

# venv Python
$py = Join-Path $venv "Scripts/python.exe"
if (-not (Test-Path $py)) { throw "Missing venv python at $py" }

# Upgrade pip + wheels
& $py -m pip install --upgrade pip wheel setuptools

# Required deps (extend as needed)
$req = @(
  "pandas",
  "pyarrow",
  "jsonschema",
  "tabulate",
  "matplotlib"
)
& $py -m pip install @req

Write-Host "Bootstrap complete." -ForegroundColor Green
