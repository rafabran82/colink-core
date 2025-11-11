Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (git rev-parse --show-toplevel)
Set-Location $root

# Prefer py -3.11, fall back to python
$havePy = $false
try { & py -3.11 -V | Out-Null; $havePy = $true } catch {}

$venvDir = Join-Path $root '.venv'
if (-not (Test-Path $venvDir)) {
  if ($havePy) { & py -3.11 -m venv $venvDir } else { & python -m venv $venvDir }
}

$venvPy = Join-Path $venvDir 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) { throw "Venv python not found at $venvPy" }

# Write requirements.lock as plain lines (no here-strings needed)
$reqLines = @(
  'pandas==2.2.3',
  'pyarrow==18.0.0',
  'jsonschema==4.23.0',
  'tabulate==0.9.0',
  'matplotlib==3.9.2'
)
$reqPath = Join-Path $root 'requirements.lock'
[IO.File]::WriteAllLines($reqPath, $reqLines, (New-Object System.Text.UTF8Encoding($false)))

& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r $reqPath
Write-Host "Venv ready: $venvPy" -ForegroundColor Green
