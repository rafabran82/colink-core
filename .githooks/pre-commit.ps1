Write-Host "pre-commit: byte-compile..."
Get-ChildItem -Recurse -File -Include *.py |
  Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
  ForEach-Object { python -m py_compile $_.FullName }

Write-Host "pre-commit: sim json_cli smoke..."
$env:PYTHONWARNINGS = "ignore"
pytest -q colink_core/sim/test_json_cli.py
