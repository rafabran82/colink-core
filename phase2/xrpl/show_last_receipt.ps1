param()

$dir = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) { Write-Error "Receipts folder not found: $dir"; exit 1 }

$last = Get-ChildItem (Join-Path $dir "otc-*.json") | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $last) { Write-Host "No receipts found."; exit 0 }

Write-Host "Latest receipt:`n$($last.FullName)`n" -ForegroundColor Cyan

# Read JSON (handle BOM/encodings)
$raw = Get-Content $last.FullName -Raw
try { $obj = $raw | ConvertFrom-Json } catch {
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
  $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
  $obj   = $text | ConvertFrom-Json
}

function _first { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$Vals)
  foreach ($v in $Vals) { if ($null -ne $v -and "$v" -ne '') { return $v } }
  return $null
}

# Structure can vary slightly; be tolerant.
$P = if ($obj.psobject.Properties.Name -contains 'params') { $obj.params } else { $null }
$R = if ($obj.psobject.Properties.Name -contains 'results') { $obj.results } else { $null }

$ts   = _first $obj.ts_iso $obj.ts $obj.timestamp
$qty  = if ($P) { _first $P.qty_copx $P.qty } else { $null }
$px   = if ($P) { _first $P.price_xrp $P.price } else { $null }
$slip = if ($P) { _first $P.slippage } else { $null }
$cap  = if ($P) { _first $P.cap_drops $P.cap } else { $null }

$step1eng = _first $obj.step1.engine_result
$step1h   = _first $obj.step1.hash
$step1fee = _first $obj.step1.fee_drops 0

$step2eng = _first $obj.step2.engine_result
$step2h   = _first $obj.step2.hash
$step2fee = _first $obj.step2.fee_drops 0

$makerDx  = if ($R) { _first $R.maker_delta_drops } else { $null }
$takerDx  = if ($R) { _first $R.taker_delta_drops } else { $null }
$gross    = if ($R) { _first $R.est_gross_drops }  else { $null }

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
