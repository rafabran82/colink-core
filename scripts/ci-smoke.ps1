param(
  [switch]$VerboseOutput
)

Write-Host "== CI Smoke: Python & imports =="

# Ensure Python present
python --version
if ($LASTEXITCODE -ne 0) { Write-Error "Python not available"; exit 1 }

# Upgrade pip quietly
python -m pip install --upgrade pip | Out-Null

# Install deps if present
if (Test-Path requirements.txt) { pip install -r requirements.txt }
if (Test-Path pyproject.toml)   { pip install -e . }

# Run the import-only pytest
$pytestArgs = @("-q","-k","test_imports","--maxfail=1")
if ($VerboseOutput) { $pytestArgs = @("-vv") + $pytestArgs }
python -m pytest @pytestArgs
exit $LASTEXITCODE
