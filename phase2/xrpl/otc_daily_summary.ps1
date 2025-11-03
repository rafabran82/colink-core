param()

# balances
$balPy = Join-Path $PSScriptRoot "tools\show_balances.py"
if (Test-Path $balPy) {
  Write-Host "`n== Balances ==" -ForegroundColor Cyan
  python $balPy
}

# last (rich) receipt
$show = Join-Path $PSScriptRoot "show_last_receipt.ps1"
if (Test-Path $show) {
  Write-Host "`n== Last Receipt (rich) ==" -ForegroundColor Cyan
  powershell -ExecutionPolicy Bypass -File $show -FindRich
}

# export CSV (overwrites file with all receipts)
$csv = Join-Path $PSScriptRoot "export_receipts_csv.ps1"
if (Test-Path $csv) {
  Write-Host "`n== Export CSV ==" -ForegroundColor Cyan
  powershell -ExecutionPolicy Bypass -File $csv
}

