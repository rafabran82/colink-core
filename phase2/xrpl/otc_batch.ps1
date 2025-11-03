param(
  [Parameter(Mandatory=$true)][string]$CsvPath,
  [switch]$StopOnFail
)

# Resolve paths
$CsvPath = (Resolve-Path $CsvPath).Path

# Scripts we need
$orch = Join-Path $PSScriptRoot "otc_trade_with_receipt.ps1"
$ver  = Join-Path $PSScriptRoot "verify_receipt_consistency.py"
$rcDir= Join-Path $PSScriptRoot "otc_receipts"

if (!(Test-Path $orch)) { Write-Error "Missing orchestrator: $orch"; exit 1 }
if (!(Test-Path $ver))  { Write-Error "Missing verifier: $ver"; exit 1 }
if (!(Test-Path $CsvPath)) { Write-Error "CSV not found: $CsvPath"; exit 1 }
if (!(Test-Path $rcDir)) { New-Item -ItemType Directory -Path $rcDir | Out-Null }

# Load rows (expects headers: qty_copx,price_xrp,slippage)
$rows = Import-Csv -Path $CsvPath
if (-not $rows -or $rows.Count -eq 0) { Write-Error "CSV has no rows."; exit 1 }

[int]$i = 0
[int]$ok = 0
[int]$fail = 0

foreach ($r in $rows) {
  $i++
  try {
    $qty  = [decimal]$r.qty_copx
    $px   = [decimal]$r.price_xrp
    $slip = [decimal]$r.slippage
  } catch {
    Write-Host ("`n❌ Row #{0} parse error. Ensure numeric columns: qty_copx, price_xrp, slippage." -f $i) -ForegroundColor Red
    $fail++
    if ($StopOnFail) { exit 2 }
    continue
  }

  Write-Host ("`n== TRADE #{0}: qty={1} px={2} slip={3} ==" -f $i, $qty, $px, $slip) -ForegroundColor Yellow

  try {
    powershell -ExecutionPolicy Bypass -File $orch -QtyCOPX $qty -PriceXRP $px -Slippage $slip

    if ($LASTEXITCODE -ne 0) {
      Write-Host ("❌ Trade #{0} orchestrator exit code {1}" -f $i, $LASTEXITCODE) -ForegroundColor Red
      $fail++
      if ($StopOnFail) { exit 2 }
      continue
    }

    # Verify newest receipt
    $last = Get-ChildItem (Join-Path $rcDir "otc-*.json") | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $last) {
      Write-Host ("❌ Trade #{0} produced no receipt" -f $i) -ForegroundColor Red
      $fail++
      if ($StopOnFail) { exit 2 }
      continue
    }

    $verOut = python $ver $last.FullName | ConvertFrom-Json
    if ($verOut.ok -ne $true) {
      Write-Host ("❌ Trade #{0} receipt FAIL: {1}" -f $i, $last.Name) -ForegroundColor Red
      foreach ($m in $verOut.messages) { Write-Host (" - {0}" -f $m) -ForegroundColor Yellow }
      $fail++
      if ($StopOnFail) { exit 2 }
      continue
    }

    Write-Host ("✅ Trade #{0} PASS ({1})" -f $i, $last.Name) -ForegroundColor Green
    $ok++

  } catch {
    Write-Host ("❌ Trade #{0} error: {1}" -f $i, $_.Exception.Message) -ForegroundColor Red
    $fail++
    if ($StopOnFail) { exit 2 }
  }
}

Write-Host "`n== BATCH SUMMARY ==" -ForegroundColor Cyan
Write-Host ("Completed: {0}, Failed: {1}, Total: {2}" -f $ok, $fail, $i)
if ($fail -gt 0) { exit 2 } else { exit 0 }

