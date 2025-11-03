param(
  [switch]$FindRich  # walk back to the newest receipt that contains .params/.results
)

$dir = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) { Write-Error "Receipts folder not found: $dir"; exit 1 }

$files = Get-ChildItem (Join-Path $dir "otc-*.json") | Sort-Object LastWriteTime -Descending
if (-not $files -or $files.Count -eq 0) { Write-Host "No receipts found."; exit 0 }

function Read-Json($path) {
  $raw = Get-Content $path -Raw
  try { return ($raw | ConvertFrom-Json) } catch {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
    return ($text | ConvertFrom-Json)
  }
}

# pick target file
$target = $files[0]
$obj = Read-Json $target.FullName

if ($FindRich -and -not ($obj.psobject.Properties.Name -contains 'params' -and $obj.psobject.Properties.Name -contains 'results')) {
  foreach ($f in $files) {
    $o = Read-Json $f.FullName
    if ($o.psobject.Properties.Name -contains 'params' -and $o.psobject.Properties.Name -contains 'results') {
      $target = $f
      $obj = $o
      break
    }
  }
}

Write-Host "Latest receipt:" -ForegroundColor Cyan
Write-Host "$($target.FullName)`n"

function _first { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$Vals)
  foreach ($v in $Vals) { if ($null -ne $v -and "$v" -ne '') { return $v } }
  return $null
}

$hasParams  = $obj.psobject.Properties.Name -contains 'params'
$hasResults = $obj.psobject.Properties.Name -contains 'results'

$P = if ($hasParams)  { $obj.params }  else { $null }
$R = if ($hasResults) { $obj.results } else { $null }

$ts   = _first $obj.ts_iso $obj.ts $obj.timestamp
$qty  = if ($P) { _first $P.qty_copx  $P.qty } else { $null }
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

[pscustomobject]@{`n  step1_explorer    = $obj.step1.explorer_url`n  step2_explorer    = $obj.step2.explorer_url
  ts_iso            = $ts
  schema            = if ($hasParams -and $hasResults) { 'rich' } else { 'legacy' }
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


