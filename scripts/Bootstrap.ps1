[CmdletBinding()]
param(
  [string]$Python = "python",
  [switch]$Force
)
Write-Host "==> Bootstrapping venv & dev deps..."
if ($Force -and (Test-Path ".venv")) {
  Write-Host "Removing existing .venv because -Force was specified..."
  Remove-Item -Recurse -Force ".venv"
}
if (-not (Test-Path ".venv")) {
  & $Python -m venv .venv
}
$pip = ".\.venv\Scripts\pip.exe"
$python = ".\.venv\Scripts\python.exe"

# Prefer local requirements if present
$reqs = @()
if (Test-Path "requirements-dev.txt") { $reqs += "requirements-dev.txt" }
elseif (Test-Path "requirements.txt") { $reqs += "requirements.txt" }

if ($reqs.Count -gt 0) {
  & $pip install -U pip wheel
  foreach ($r in $reqs) {
    Write-Host "Installing from $r..."
    & $pip install -r $r
  }
} else {
  Write-Host "No requirements files found; installing common dev tools only (safe to skip if you already pin these)."
  & $pip install -U pip wheel
  & $pip install pytest ruff black matplotlib numpy pandas
}
Write-Host "Bootstrap complete."

