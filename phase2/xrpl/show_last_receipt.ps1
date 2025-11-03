param()

$dir = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) {
  Write-Error "Receipts folder not found: $dir"
  exit 1
}
$last = Get-ChildItem (Join-Path $dir "otc-*.json") | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $last) {
  Write-Host "No receipts found."
  exit 0
}
Write-Host "Latest receipt:`n$($last.FullName)`n" -ForegroundColor Cyan

# Read JSON (handles BOM if any)
$raw = Get-Content $last.FullName -Raw
try { $obj = $raw | ConvertFrom-Json } catch {
  # fallback for odd encodings
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
  $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
  $obj   = $text | ConvertFrom-Json
}

# Params live under .params
$qty      = $obj.params.qty_copx
$px       = $obj.params.price_xrp
$slip     = $obj.params.slippage
$cap      = $obj.params.cap_drops
$step1eng = $obj.step1.engine_result
$step1h   = $obj.step1.hash
$step1fee = $obj.step1.fee_drops
$step2eng = $obj.step2.engine_result
$step2h   = $obj.step2.hash
$step2fee = $obj.step2.fee_drops
$makerDx  = $obj.results.maker_delta_drops
$takerDx  = $obj.results.taker_delta_drops
$gross    = $obj.results.est_gross_drops
$ts       = $obj.ts_iso

[pscustomobject]@{
  ts_iso            = $ts
  qty_copx          = $qty
  price_xrp         = $px
  slippage          = $slip
  cap_drops         = $cap
  step1_engine      = $step1eng
  step1_hash        = $step1h
  step1_fee_drops   = $step1fee
  step2_engine      = $step2eng
  step2_hash        = $step2h
  step2_fee_drops   = $step2fee
  maker_delta_drops = $makerDx
  taker_delta_drops = $takerDx
  est_gross_drops   = $gross
} | Format-List
