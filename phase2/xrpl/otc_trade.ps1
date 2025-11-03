param(
  [double]$PriceXRP = 0.004,   # price XRP per 1 COPX
  [double]$Slippage = 0.02,     # 2% headroom
  [int]   $Cushion  = 20,       # a few extra drops
  [int]   $QtyCOPX  = 250       # amount of COPX taker buys OTC
)

# Reload .env into this process (so python sees these values)
Get-Content .env.testnet |
  ? { $_ -match '^\s*[^#=\s]+\s*=' } |
  % { $k,$v = $_ -split '=',2; [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim(), 'Process') }

# Compute XRP cap in drops: ceil(qty * price * 1e6 * (1+slippage)) + cushion
$capDrops = [int][math]::Ceiling($QtyCOPX * $PriceXRP * 1000000 * (1 + $Slippage)) + $Cushion

Write-Host "== OTC PARAMETERS ==" -ForegroundColor Cyan
"{0,-18} {1}" -f "QtyCOPX:",       $QtyCOPX
"{0,-18} {1}" -f "Best Price XRP:", $PriceXRP
"{0,-18} {1:P2}" -f "Slippage:",    $Slippage
"{0,-18} {1}" -f "Cap Drops:",      $capDrops

Write-Host "`n== BEFORE ==" -ForegroundColor Cyan
python .\phase2\xrpl\tools\show_balances.py

# STEP 1: Taker pays XRP to Maker
$env:OTC_XRP_DROPS = "$capDrops"
Write-Host "`n== STEP 1: TAKER pays XRP to MAKER ==" -ForegroundColor Yellow
python .\phase2\xrpl\otc_step1_taker_pays_xrp.py

# STEP 2: Issuer mints/sends COPX to Taker
$env:OTC_COPX_QTY = "$QtyCOPX"
Write-Host "`n== STEP 2: ISSUER pays COPX to TAKER ==" -ForegroundColor Yellow
python .\phase2\xrpl\otc_step2_issuer_pays_copx.py

Write-Host "`n== AFTER ==" -ForegroundColor Cyan
python .\phase2\xrpl\tools\show_balances.py
