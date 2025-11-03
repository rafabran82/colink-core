param()

$dir = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) { Write-Error "Receipts folder not found: $dir"; exit 1 }
$last = Get-ChildItem (Join-Path $dir "otc-*.json") | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $last) { Write-Host "No receipts found."; exit 0 }

$py = Join-Path $PSScriptRoot "verify_receipt_consistency.py"
if (!(Test-Path $py)) { Write-Error "Missing verify_receipt_consistency.py"; exit 1 }

$out = python $py $last.FullName | ConvertFrom-Json
if ($out.ok -eq $true) {
  Write-Host "✅ PASS: $($last.Name)" -ForegroundColor Green
} else {
  Write-Host "❌ FAIL: $($last.Name)" -ForegroundColor Red
  $out.messages | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
}

