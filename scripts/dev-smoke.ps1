$ErrorActionPreference = "Stop"

Write-Host "== Byte-compile ==" -ForegroundColor Cyan
Get-ChildItem -Recurse -File -Include *.py |
  Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
  ForEach-Object { python -m py_compile $_.FullName }

Write-Host "== Editable install ==" -ForegroundColor Cyan
pip install -e .

Write-Host "== CLI: version, quote, sweep ==" -ForegroundColor Cyan
colink-json --version
colink-json quote --col-in 8000 --min-out-bps 150 --twap-guard
colink-json sweep --outdir charts

Write-Host "== Tests ==" -ForegroundColor Cyan
pytest -q
