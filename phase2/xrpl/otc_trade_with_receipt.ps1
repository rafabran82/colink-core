param(
  [double]$PriceXRP = 0.004,
  [double]$Slippage = 0.02,
  [int]   $Cushion  = 20,
  [int]   $QtyCOPX  = 250
)

# Load .env into this process
Get-Content .env.testnet |
  ? { $_ -match '^\s*[^#=\s]+\s*=' } |
  % { $k,$v = $_ -split '=',2; [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim(), 'Process') }

# Compute XRP cap (drops)
$capDrops = [int][math]::Ceiling($QtyCOPX * $PriceXRP * 1000000 * (1 + $Slippage)) + $Cushion

# Pre snapshot
$before = python .\phase2\xrpl\tools\show_balances.py | Out-String | ConvertFrom-Json

# Step 1 – taker pays XRP to maker
$env:OTC_XRP_DROPS = "$capDrops"
$step1Raw = python .\phase2\xrpl\otc_step1_taker_pays_xrp.py | Out-String
$step1    = $step1Raw | ConvertFrom-Json

# Step 2 – issuer pays COPX to taker
$env:OTC_COPX_QTY = "$QtyCOPX"
$step2Raw = python .\phase2\xrpl\otc_step2_issuer_pays_copx.py | Out-String
$step2    = $step2Raw | ConvertFrom-Json

# Post snapshot
$after = python .\phase2\xrpl\tools\show_balances.py | Out-String | ConvertFrom-Json

# Build receipt
$receipt = [ordered]@{
  ts_iso    = (Get-Date).ToString("s")
  params    = [ordered]@{
    qty_copx   = $QtyCOPX
    price_xrp  = $PriceXRP
    slippage   = $Slippage
    cap_drops  = $capDrops
  }
  before    = $before
  step1     = $step1
  step2     = $step2
  after     = $after
}

# Ensure receipts folder
$root = Join-Path $PSScriptRoot "otc_receipts"
if (!(Test-Path $root)) { New-Item -ItemType Directory -Path $root | Out-Null }

# Save file
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$path  = Join-Path $root ("otc-{0}.json" -f $stamp)
$receipt | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $path

Write-Host "Saved receipt:" -ForegroundColor Green
Write-Host $path
