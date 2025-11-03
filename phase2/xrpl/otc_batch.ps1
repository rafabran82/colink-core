param(
  [Parameter(Mandatory=$true)][string]$CsvPath
)

# Resolve paths
$CsvPath = (Resolve-Path $CsvPath).Path

# Orchestrator script (single trade)
$orch = Join-Path $PSScriptRoot "otc_trade_with_receipt.ps1"
if (!(Test-Path $orch)) { Write-Error "Missing orchestrator: $orch"; exit 1 }

if (!(Test-Path $CsvPath)) { Write-Error "CSV not found: $CsvPath"; exit 1 }

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
    Write-Host "`n❌ Row #$i parse error. Ensure numeric columns: qty_copx, price_xrp, slippage." -ForegroundColor Red
    $fail++
    continue
  }

  Write-Host ("`n== TRADE #{0}: qty={1} px={2} slip={3} ==" -f $i, $qty, $px, $slip) -ForegroundColor Yellow
  try {
    powershell -ExecutionPolicy Bypass -File $orch -QtyCOPX $qty -PriceXRP $px -Slippage $slip
    if ($LASTEXITCODE -ne 0) {
      Write-Host ("❌ Trade #{0} failed with exit code {1}" -f $i, $LASTEXITCODE) -ForegroundColor Red
      $fail++
    } else {
      Write-Host ("✅ Trade #{0} completed" -f $i) -ForegroundColor Green
      $ok++
    }
  } catch {
    Write-Host ("❌ Trade #{0} error: {1}" -f $i, $_.Exception.Message) -ForegroundColor Red
    $fail++
  }
}

Write-Host "`n== BATCH SUMMARY ==" -ForegroundColor Cyan
Write-Host ("Completed: {0}, Failed: {1}, Total: {2}" -f $ok, $fail, $i)
if ($fail -gt 0) { exit 2 } else { exit 0 }
