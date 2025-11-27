[CmdletBinding()]
param([switch]$NoCompile)
$ErrorActionPreference = "Stop"
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  Write-Error "Python venv not found. Run: scripts\\Bootstrap.ps1"
}

if (-not $NoCompile) {
  Write-Host "==> Byte-compiling Python (excluding .venv)..."
  Get-ChildItem -Recurse -File -Include *.py `
    | Where-Object { $_.FullName -notmatch '\\\.venv\\' } `
    | ForEach-Object { & $python -m py_compile $_.FullName }
}

Write-Host "==> Running tests..."
& ".\.venv\Scripts\pytest.exe" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Tests passed."

