param(
  [switch]$FindRich
)

# Quiet xrpay name warnings (local only)
$__oldWarnPref = $WarningPreference
try {
  $WarningPreference = 'SilentlyContinue'
  Import-Module xrpay -DisableNameChecking -ErrorAction SilentlyContinue
} finally {
  $WarningPreference = $__oldWarnPref
}

$dir = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) { Write-Error "Receipts folder not found: $dir"; exit 1 }

# Helper: read JSON tolerant of BOM / odd encodings
function Read-JsonTolerant([string]$path) {
  $raw = Get-Content -LiteralPath $path -Raw
  try { return $raw | ConvertFrom-Json } catch {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
    return ($text | ConvertFrom-Json)
  }
}

# Choose file
$files = Get-ChildItem (Join-Path $dir "otc-*.json") | Sort-Object LastWriteTime -Descending
if (-not $files -or $files.Count -eq 0) { Write-Host "No receipts found."; exit 0 }

$chosen = $null
if ($FindRich) {
  foreach ($f in $files) {
    $objTry = Read-JsonTolerant $f.FullName
    if ($objTry.schema -and "$($objTry.schema)".Trim() -ne "") { $chosen = $f; break }
  }
  if (-not $chosen) { $chosen = $files[0] }  # fallback
} else {
  $chosen = $files[0]
}

$obj = Read-JsonTolerant $chosen.FullName

# Normalize fields across schemas
$schema   = if ($obj.schema) { "$($obj.schema)" } else { "legacy" }
$ts       = if ($obj.ts_iso) { "$($obj.ts_iso)" } else { "" }

# params (rich) or legacy top-level
$qty      = $null
$px       = $null
$slip     = $null
$cap      = $null
if ($obj.params) {
  $qty  = $obj.params.qty_copx
  $px   = $obj.params.price_xrp
  $slip = $obj.params.slippage
  $cap  = $obj.params.cap_drops
} else {
  $qty  = $obj.qty_copx
  $px   = $obj.price_xrp
  $slip = $obj.slippage
  $cap  = $obj.cap_drops
}

# step 1 / step 2 blocks (rich); legacy may have partials
$step1eng = $obj.step1.engine_result
$step1h   = $obj.step1.hash
$step1fee = $obj.step1.fee_drops
$step1url = $obj.step1.explorer_url

$step2eng = $obj.step2.engine_result
$step2h   = $obj.step2.hash
$step2fee = $obj.step2.fee_drops
$step2url = $obj.step2.explorer_url

# results (rich) or legacy top-level approximations
$makerDx  = $null
$takerDx  = $null
$gross    = $null
if ($obj.results) {
  $makerDx = $obj.results.maker_delta_drops
  $takerDx = $obj.results.taker_delta_drops
  $gross   = $obj.results.est_gross_drops
} else {
  $makerDx = $obj.maker_delta_drops
  $takerDx = $obj.taker_delta_drops
  $gross   = $obj.est_gross_drops
}

Write-Host "Latest receipt:`n$($chosen.FullName)`n" -ForegroundColor Cyan

[pscustomobject]@{
  ts_iso            = $ts
  schema            = $schema
  qty_copx          = $qty
  price_xrp         = $px
  slippage          = $slip
  cap_drops         = $cap
  step1_engine      = $step1eng
  step1_hash        = $step1h
  step1_fee_drops   = $step1fee
  step1_explorer    = $step1url
  step2_engine      = $step2eng
  step2_hash        = $step2h
  step2_fee_drops   = $step2fee
  step2_explorer    = $step2url
  maker_delta_drops = $makerDx
  taker_delta_drops = $takerDx
  est_gross_drops   = $gross
} | Format-List
