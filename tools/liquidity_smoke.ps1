param(
  [string]$Issuer = "rBvZJP5WNGipMyScwFGFmDRAvcaFyn3LBY",
  [int]   $DropsPerCOPX = 250,   # 0.00025 XRP/COPX
  [int]   $TakeCOPX = 50,        # size of the test-cross bid (set 0 to skip placing)
  [switch]$SkipPlace               # if set, just report books (no crossing bid)
)

$ErrorActionPreference = "Stop"
if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }

# 160-bit code for "COPX"
$COPX = @{ currency = "434F505800000000000000000000000000000000"; issuer = $Issuer }

# Require helper
$bookHelper = Join-Path $PSScriptRoot "xrpl_book.ps1"
if (-not (Test-Path $bookHelper)) { throw "Missing $bookHelper. Commit added earlier." }
. $bookHelper

function Show-XrpCopx {
  param([int]$Limit = 10)
  Write-Host "`n== XRP/COPX (bids: pay COPX, get XRP) ==" -ForegroundColor Cyan
  $bids = Invoke-BookOffers -taker_gets @{currency='XRP'} -taker_pays $COPX -limit $Limit
  # quality here is XRP per COPX (decimal), so just show it directly
  $bids | Select-Object Account,Sequence,@{n='xrp_per_copx';e={$_.quality}} |
    Format-Table -Auto
}

function Show-CopxXrp {
  param([int]$Limit = 10)
  Write-Host "`n== COPX/XRP (asks: sell COPX, take XRP) ==" -ForegroundColor Yellow
  $asks = Invoke-BookOffers -taker_gets $COPX -taker_pays @{currency='XRP'} -limit $Limit
  # quality here is "drops per COPX" (usually integer).
  $asks | Select-Object Account,Sequence,
    @{n='drops_per_copx';e={$_.quality}},
    owner_funds,taker_gets_funded,taker_pays_funded |
    Format-Table -Auto
}

Show-XrpCopx
Show-CopxXrp

if ($SkipPlace -or $TakeCOPX -le 0) {
  Write-Host "`n(Skipping placement step.)" -ForegroundColor DarkGray
  exit 0
}

# Ensure bidder is set
$seed = $env:BIDDER_SEED
if (-not $seed) { $seed = $env:TAKER_SEED }
if (-not $seed) { throw "Set BIDDER_SEED (or TAKER_SEED) for the crossing bid." }

# 1) Ensure trust line exists
python (Join-Path $PSScriptRoot "..\phase2\xrpl\make_trustline.py") --issuer $Issuer | Out-Null

# 2) Place a tiny bid at the target price
$drops = [string]($DropsPerCOPX * $TakeCOPX)
python (Join-Path $PSScriptRoot "..\phase2\xrpl\make_bid_xrp_for_copx.py") `
  --issuer $Issuer --value $TakeCOPX --drops $drops | Out-Null

Start-Sleep -Seconds 2

Write-Host "`n== Books after crossing bid ==" -ForegroundColor Green
Show-XrpCopx
Show-CopxXrp
