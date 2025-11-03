param(
  [string]$Folder = "$(Join-Path $PSScriptRoot 'otc_receipts')"
)
if (!(Test-Path $Folder)) {
  Write-Error "Receipts folder not found: $Folder"
  exit 1
}
$files = Get-ChildItem -Path $Folder -Filter 'otc-*.json' | Sort-Object LastWriteTime -Descending
if ($files.Count -eq 0) {
  Write-Error "No receipts found in $Folder"
  exit 2
}
$path = $files[0].FullName
$rec  = Get-Content $path | ConvertFrom-Json

Write-Host "Latest receipt:" -ForegroundColor Cyan
Write-Host $path

$qty    = [decimal]$rec.params.qty_copx
$price  = [double]$rec.params.price_xrp
$slip   = [double]$rec.params.slippage
$cap    = [int64]$rec.params.cap_drops

$makerBeforeDrops = [int64]$rec.before.maker.xrp_drops
$takerBeforeDrops = [int64]$rec.before.taker.xrp_drops
$makerAfterDrops  = [int64]$rec.after.maker.xrp_drops
$takerAfterDrops  = [int64]$rec.after.taker.xrp_drops

$makerDeltaDrops = $makerAfterDrops - $makerBeforeDrops
$takerDeltaDrops = $takerAfterDrops - $takerBeforeDrops

$step1 = $rec.step1
$step2 = $rec.step2

$estXrp = [decimal]$qty * [decimal]$price
$estDrops = [int64][math]::Round($estXrp * 1000000)

[pscustomobject]@{
  ts_iso                = $rec.ts_iso
  qty_copx              = $qty
  price_xrp             = $price
  slippage              = $slip
  cap_drops             = $cap
  step1_engine          = $step1.engine_result
  step1_hash            = $step1.hash
  step2_engine          = $step2.engine_result
  step2_hash            = $step2.hash
  maker_delta_drops     = $makerDeltaDrops
  taker_delta_drops     = $takerDeltaDrops
  est_gross_drops       = $estDrops
} | Format-List
