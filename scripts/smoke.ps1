param(
  [string]$Repo = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

# Resolve Python in repo venv first, fall back to system python
$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# Install dev deps (quiet) from pinned file
$req = Join-Path $Repo "requirements-dev.txt"
& $py -m pip install -q -r $req | Out-Null

# Run pytest from the repo root and capture output into artifacts
Push-Location $Repo
try {
  $art = Join-Path $Repo ".artifacts"
  New-Item -ItemType Directory -Force -Path $art | Out-Null

  # Ensure pytest is available even if requirements file changes later
  if (-not (Test-Path ".\.venv\Scripts\pytest.exe")) {
    & $py -m pip install -q pytest | Out-Null
  }

  & $py -m pytest -q . --import-mode=importlib *>&1 `
    | Tee-Object -FilePath (Join-Path $art "pytest.txt") | Out-Null
}
finally {
  Pop-Location
}
