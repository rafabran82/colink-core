param()
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repo = Split-Path $PSScriptRoot -Parent
Push-Location $repo
try {
  # Prefer venv python if present
  $py = if (Test-Path .\.venv\Scripts\python.exe) { ".\.venv\Scripts\python.exe" } else { "python" }

  # Ensure artifacts folder for pytest log
  if (-not (Test-Path .\.artifacts)) { New-Item -ItemType Directory -Force -Path .\.artifacts | Out-Null }

  # Minimal deps for our tests
  & $py -m pip install -q pytest fastapi httpx "pydantic-settings>=2" python-dotenv | Out-Null

  # Run pytest in importlib mode so path aliasing can’t bite us
  & $py -m pytest -q . --import-mode=importlib *>&1 | Tee-Object -File .\.artifacts\pytest.txt
}
finally {
  Pop-Location
}
