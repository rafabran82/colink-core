param(
  [switch]$FindRich
)

function Read-JsonTolerant([string]$path) {
  $raw = Get-Content $path -Raw
  try { return ($raw | ConvertFrom-Json) } catch {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $text  = [System.Text.Encoding]::UTF8.GetString($bytes)
    return ($text | ConvertFrom-Json)
  }
}

$dir = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) { Write-Error "Receipts folder not found: $dir"; exit 1 }

$files = Get-ChildItem (Join-Path $dir "otc-*.json") | Sort-Object LastWriteTime -Descending
if (-not $files -or $files.Count -eq 0) { Write-Host "No receipts found."; exit 0 }

# Choose file: newest OR newest that looks "rich"
$chosen = $null
if ($FindRich) {
  foreach ($f in $files) {
    $o = Read-JsonTolerant $f.FullName
    if ($o.schema -or $o.params -or $o.results) { $chosen = $f; break }
  }
  if (-not $chosen) { $chosen = $files[0] } # fallback
} else {
  $chosen = $files[0]
}

$obj = Read-JsonTolerant $chosen.FullName

# Detect schema type
$schemaKind = if ($obj.schema -or $obj.params -or $obj.results) { "rich" } else { "legacy" }

# Extract core fields with fallbacks
if ($schemaKind -eq "rich") {
  $ts      = $obj.ts_iso
  $qty     = $obj.params.qty_copx
  $px      = $obj.params.price_xrp
  $slip    = $obj.params.slippage
  $cap     = $obj.params.cap_drops
  $s1      = $obj.step1
  $s2      = $obj.step2
  $mDelta  = $obj.results.maker_delta_drops
  $tDelta  = $obj.results.taker_delta_drops
  $gross   = $obj.results.est_gross_drops
} else {
  # legacy fields
  $ts      = $obj.ts_iso
  if (-not $ts) { $ts = $obj.timestamp }  # your legacy uses "timestamp"
  $qty     = $obj.qty_copx
  $px      = $obj.price_xrp
  $slip    = $obj.slippage
  $cap     = $obj.cap_drops
  $s1      = $obj.step1
  $s2      = $obj.step2

  # compute deltas from balances.before/after if available
  $mDelta = $null; $tDelta = $null; $gross = $null
  if ($obj.balances -and $obj.balances.before -and $obj.balances.after) {
    $mBefore = $obj.balances.before.maker.xrp_drops
    $mAfter  = $obj.balances.after.maker.xrp_drops
    $tBefore = $obj.balances.before.taker.xrp_drops
    $tAfter  = $obj.balances.after.taker.xrp_drops
    if ($mBefore -ne $null -and $mAfter -ne $null) { $mDelta = [int64]($mAfter - $mBefore) }
    if ($tBefore -ne $null -and $tAfter -ne $null) { $tDelta = [int64]($tAfter - $tBefore) }
  }

  # gross (approx) if not present: qty * px * 1e6 (drops)
  if ($qty -and $px) {
    try { $gross = [int64]([math]::Round(([decimal]$qty * [decimal]$px) * 1000000)) } catch { }
  }
}

# Build explorer URLs if missing (you’re on testnet)
function Make-Explorer([string]$hash) {
  if (-not $hash) { return $null }
  return "https://testnet.xrpl.org/transactions/$hash"
}

$step1Explorer = $null
$step2Explorer = $null
if ($s1) {
  $step1Explorer = $s1.explorer_url
  if (-not $step1Explorer) { $step1Explorer = Make-Explorer $s1.hash }
}
if ($s2) {
  $step2Explorer = $s2.explorer_url
  if (-not $step2Explorer) { $step2Explorer = Make-Explorer $s2.hash }
}

Write-Host "Latest receipt:`n$($chosen.FullName)`n" -ForegroundColor Cyan

[pscustomobject]@{
  ts_iso            = $ts
  schema            = $schemaKind
  qty_copx          = $qty
  price_xrp         = $px
  slippage          = $slip
  cap_drops         = $cap

  step1_engine      = $s1.engine_result
  step1_hash        = $s1.hash
  step1_fee_drops   = $s1.fee_drops
  step1_explorer    = $step1Explorer

  step2_engine      = $s2.engine_result
  step2_hash        = $s2.hash
  step2_fee_drops   = $s2.fee_drops
  step2_explorer    = $step2Explorer

  maker_delta_drops = $mDelta
  taker_delta_drops = $tDelta
  est_gross_drops   = $gross
} | Format-List
