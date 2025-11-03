param(
  [Parameter(Mandatory=$true)][decimal]$QtyCOPX,
  [Parameter(Mandatory=$true)][decimal]$PriceXRP,
  [Parameter(Mandatory=$true)][decimal]$Slippage
)

# Quiet import of xrpay
$__oldWarnPref = $WarningPreference
try {
  $WarningPreference = 'SilentlyContinue'
  Import-Module xrpay -DisableNameChecking -ErrorAction SilentlyContinue
} finally { $WarningPreference = $__oldWarnPref }

# Fail-fast if core envs missing
$req = @("XRPL_TAKER_ADDRESS","XRPL_TAKER_SEED","XRPL_MAKER_ADDRESS","XRPL_ISSUER_ADDRESS","XRPL_ISSUER_SEED")
$miss = $req | Where-Object { [string]::IsNullOrWhiteSpace([System.Environment]::GetEnvironmentVariable($_)) }
if ($miss.Count -gt 0) { throw "Missing environment variables: $($miss -join ', ')" }

# XRPL RPC default (testnet) if not set
if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }

$WorstPx   = [decimal]$PriceXRP * (1 + [decimal]$Slippage)
$CapDrops  = [int]([math]::Ceiling($QtyCOPX * $WorstPx * 1000000)) + 10
$env:OTC_XRP_DROPS = "$CapDrops"
$env:OTC_COPX_QTY  = "$QtyCOPX"

Write-Warning ("Cap drops = {0} at worst={1} XRP/COPX" -f $CapDrops, [decimal]::Round($WorstPx, 8))

function Invoke-PyJson([string]$path) {
  $out = & python $path 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $out) { throw "Python failed: $path" }
  try { return ($out | ConvertFrom-Json) } catch { throw "Bad JSON from: $path`n$out" }
}

# Balances BEFORE
$showBal = Join-Path $PSScriptRoot "tools\show_balances.py"
$before  = Invoke-PyJson $showBal

# STEP 1 — taker pays XRP
$step1Py = Join-Path $PSScriptRoot "otc_step1_taker_pays_xrp.py"
$p1      = Invoke-PyJson $step1Py
if ($p1.engine_result -ne "tesSUCCESS" -or -not $p1.hash) { throw "STEP1 failed: $(($p1 | ConvertTo-Json -Depth 6))" }

# STEP 2 — issuer pays COPX
$step2Py = Join-Path $PSScriptRoot "otc_step2_issuer_pays_copx.py"
$p2      = Invoke-PyJson $step2Py
if ($p2.engine_result -ne "tesSUCCESS" -or -not $p2.hash) { throw "STEP2 failed: $(($p2 | ConvertTo-Json -Depth 6))" }

# Balances AFTER
$after = Invoke-PyJson $showBal

# Deltas / gross estimate
[int64]$mDelta = 0; [int64]$tDelta = 0
try {
  $mDelta = [int64]($after.maker.xrp_drops - $before.maker.xrp_drops)
  $tDelta = [int64]($after.taker.xrp_drops - $before.taker.xrp_drops)
} catch { }

[int64]$estGross = 0
try { $estGross = [int64]([math]::Round(([decimal]$QtyCOPX * [decimal]$PriceXRP) * 1000000)) } catch { }

# Rich receipt (schema=1.0)
$ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
$receipt = [pscustomobject]@{
  schema = "1.0"
  ts_iso = $ts
  params = @{
    qty_copx   = "$QtyCOPX"
    price_xrp  = "$PriceXRP"
    slippage   = "$Slippage"
    cap_drops  = $CapDrops
  }
  step1 = @{
    engine_result  = $p1.engine_result
    hash           = $p1.hash
    fee_drops      = $p1.fee_drops
    xrp_drops_sent = $p1.xrp_drops_sent
    explorer_url   = ("https://testnet.xrpl.org/transactions/{0}" -f $p1.hash)
  }
  step2 = @{
    engine_result  = $p2.engine_result
    hash           = $p2.hash
    fee_drops      = $p2.fee_drops
    issuer_sent    = $p2.issuer_sent
    explorer_url   = ("https://testnet.xrpl.org/transactions/{0}" -f $p2.hash)
  }
  results = @{
    maker_delta_drops = $mDelta
    taker_delta_drops = $tDelta
    est_gross_drops   = $estGross
  }
}

# Save JSON (UTF-8)
$dir  = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$fname = "otc-{0}.json" -f (Get-Date).ToString("yyyyMMdd-HHmmss")
$path  = Join-Path $dir $fname

$receipt | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $path
Write-Host "Saved receipt:`n$path"
