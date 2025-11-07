# Windows/json_cli smoke: fail fast, no flakiness
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Ensure repo root
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

# Make Python see the package from source (workflow also sets PYTHONPATH)
$env:PYTHONPATH = $RepoRoot

Write-Host "Python:" (python --version)
Write-Host "Git:" (git --version)
Write-Host "Repo root:" $RepoRoot
Write-Host "PYTHONPATH:" $env:PYTHONPATH

Write-Host ">> json_cli --help"
python -m colink_core.sim.json_cli --help | Out-String | Write-Host

Write-Host ">> json_cli quote"
$q = python -m colink_core.sim.json_cli quote --col-in 100 --min-out-bps 5
Write-Host $q
if (-not ($q -match '"copx_out"')) { throw "quote output missing 'copx_out'" }

Write-Host ">> json_cli sweep"
New-Item -ItemType Directory -Force -Path charts | Out-Null
$s = python -m colink_core.sim.json_cli sweep --outdir charts --n-paths 3 --n-steps 5
Write-Host $s
if (-not ($s -match '"charts"')) { throw "sweep output missing 'charts' key" }

Write-Host "OK: json_cli smoke passed on Windows."