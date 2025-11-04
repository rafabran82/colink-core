# colink-core quick dev guide

## Smoke
colink-json quote --col-in 8000 --min-out-bps 150 --twap-guard
colink-json sweep --outdir charts

## Tests
pytest -q

## Pre-commit
Git runs a pre-commit hook that byte-compiles all .py files and runs sim JSON smoke.
If it fails, fix code or run:
  python -m py_compile path/to/file.py
  pytest -q colink_core/sim/test_json_cli.py

## Charts
Charts PNGs are ignored by git. Clean up:
  pwsh scripts/clean-charts.ps1rnrn## Quick smoke (Windows)

```powershell
pwsh scripts/dev-smoke.ps1
rn## Quick smoke — Windows

```powershell
# From repo root
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Bootstrap.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Format.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Invoke-Tests.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Invoke-Sweep.ps1 -OutDir artifacts\charts -RunName dev-smoke
