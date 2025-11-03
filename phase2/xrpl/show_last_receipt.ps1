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

# Helper: classify + completeness
function Classify([object]$o) {
  $richish  = ($o.schema -or $o.params -or $o.results)
  $hasS1    = ($o.step1 -and $o.step1.hash)
  $hasS2    = ($o.step2 -and $o.step2.hash)
  $complete = ($hasS1 -or $hasS2)
  if ($richish) { if ($complete) { return "rich-complete" } else { return "rich-incomplete" } }
  return "legacy"
}

$chosen = $null
if ($FindRich) {
  # 1) newest rich-complete; 2) fallback to newest rich-incomplete; 3) fallback to newest file
  foreach ($f in $files) { $o = Read-JsonTolerant $f.FullName; if ((Classify $o) -eq "rich-complete") { $chosen = $f; break } }
  if (-not $chosen) { foreach ($f in $files) { $o = Read-JsonTolerant $f.FullName; if ((Classify $o) -eq "rich-incomplete") { $chosen = $f; break } } }
  if (-not $chosen) { $chosen = $files[0] }
} else {
  $chosen = $files[0]
}

$obj = Read-JsonTolerant $chosen.FullName
$schemaKind = Classify $obj

# Extract + back-fill
if ($schemaKind -like "rich*") {
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
  # legacy
  $ts   = $obj.ts_iso; if (-not $ts) { $ts = $obj.timestamp }
  $qty  = $obj.qty_copx
  $px   = $obj.price_xrp
  $slip = $obj.slippage
  $cap  = $obj.cap_drops
  $s1   = $obj.step1
  $s2   = $obj.step2

  $mDelta = $null; $tDelta = $null; $gross = $null
  if ($obj.balances -and $obj.balances.before -and $obj.balances.after) {
    $mBefore = $obj.balances.before.maker.xrp_drops
    $mAfter  = $obj.balances.after.maker.xrp_drops
    $tBefore = $obj.balances.before.taker.xrp_drops
    $tAfter  = $obj.balances.after.taker.xrp_drops
    if ($mBefore -ne $null -and $mAfter -ne $null) { $mDelta = [int64]($mAfter - $mBefore) }
    if ($tBefore -ne $null -and $tAfter -ne $null) { $tDelta = [int64]($tAfter - $tBefore) }
  }
  if ($qty -and $px) {
    try { $gross = [int64]([math]::Round(([decimal]$qty * [decimal]$px) * 1000000)) } catch { }
  }
}

# Explorer URLs (build from hashes if missing)
function Make-Explorer([string]$hash) {
  if (-not $hash) { return $null }
  return "https://testnet.xrpl.org/transactions/$hash"
}
$step1Explorer = $null; $step2Explorer = $null
if ($s1) { $step1Explorer = $s1.explorer_url; if (-not $step1Explorer) { $step1Explorer = Make-Explorer $s1.hash } }
if ($s2) { $step2Explorer = $s2.explorer_url; if (-not $step2Explorer) { $step2Explorer = Make-Explorer $s2.hash } }

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
