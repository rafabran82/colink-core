# Windows/json_cli smoke: fail fast, no flakiness (no pytest)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Ensure repo root
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

# Make Python see the package from source (workflow also sets PYTHONPATH)
$env:PYTHONPATH = $RepoRoot

Write-Host "=== ENV ==="
Write-Host ("OS: " + [System.Environment]::OSVersion.VersionString)
Write-Host ("Repo root: " + $RepoRoot)
Write-Host ("pwd: " + (Get-Location))
Write-Host ("PYTHONPATH: " + $env:PYTHONPATH)
Write-Host "Top-level files:"
Get-ChildItem -Force | Select-Object Mode,Length,Name | Format-Table | Out-String | Write-Host

Write-Host "=== Versions ==="
Write-Host ("Python: " + (python --version))
Write-Host ("Git: " + (git --version))

Write-Host "=== Import sanity ==="
$pyOut = python - <<'PYCODE'
import importlib
m = importlib.import_module('colink_core.sim.json_cli')
print('import_ok:', bool(m))
print('prog:', getattr(m, 'PROG', 'colink-json'))
PYCODE
$pyOut | Out-String | Write-Host
if ($pyOut -notmatch 'import_ok: True') { throw "Python import failed for colink_core.sim.json_cli" }

Write-Host "=== CLI help ==="
python -m colink_core.sim.json_cli --help | Out-String | Write-Host

Write-Host "=== CLI quote ==="
$q = python -m colink_core.sim.json_cli quote --col-in 100 --min-out-bps 5
Write-Host $q
if (-not ($q -match '"copx_out"')) { throw "quote output missing 'copx_out'" }

Write-Host "=== CLI sweep ==="
New-Item -ItemType Directory -Force -Path charts | Out-Null
$s = python -m colink_core.sim.json_cli sweep --outdir charts --n-paths 3 --n-steps 5
Write-Host $s
if (-not ($s -match '"charts"')) { throw "sweep output missing 'charts' key" }

Write-Host "OK: json_cli smoke passed on Windows."