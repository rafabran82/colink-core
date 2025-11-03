param(
  [string]$Issuer = "rBvZJP5WNGipMyScwFGFmDRAvcaFyn3LBY",
  [int]$Limit = 20
)
$ErrorActionPreference = "Stop"

# RPC default (testnet if unset)
if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }
$rpc = $env:XRPL_RPC

# 160-bit "COPX"
$code160 = "434F505800000000000000000000000000000000"
$copx = @{ currency = $code160; issuer = $Issuer }

function Invoke-BookOffers {
  param($taker_gets, $taker_pays, [int]$limit = 20)
  $req = @{ method="book_offers"; params=@(@{taker_gets=$taker_gets; taker_pays=$taker_pays; limit=$limit}) }
  $res = Invoke-RestMethod -Method Post -Uri $rpc -ContentType 'application/json' -Body ($req | ConvertTo-Json -Depth 10)
  return $res.result.offers
}

# ---------- BIDS: taker_gets XRP, taker_pays COPX ----------
"`n== XRP/COPX (bids: pay COPX, get XRP) ==" | Write-Host
$bidOffers = Invoke-BookOffers -taker_gets @{currency="XRP"} -taker_pays $copx -limit $Limit

# quality for bids here is ~ XRP per COPX (e.g., 0.00025)
$bidRows = $bidOffers | ForEach-Object {
  [pscustomobject]@{
    Account      = $_.Account
    Sequence     = $_.Sequence
    xrp_per_copx = [double]$_.quality
  }
}
if ($bidRows) {
  $bidRows | Format-Table -AutoSize
} else {
  "(no bids)" | Write-Host
}

# ---------- ASKS: taker_gets COPX, taker_pays XRP ----------
"`n`n== COPX/XRP (asks: sell COPX, take XRP) ==" | Write-Host
$askOffers = Invoke-BookOffers -taker_gets $copx -taker_pays @{currency="XRP"} -limit $Limit

# quality for asks * 1e6 ≈ drops per COPX (e.g., 250)
$askRows = $askOffers | ForEach-Object {
  $dropsPer = [int]([double]$_.quality * 1000000)
  [pscustomobject]@{
    Account            = $_.Account
    Sequence           = $_.Sequence
    drops_per_copx     = $dropsPer
    owner_funds        = $_.owner_funds
    taker_gets_funded  = $_.taker_gets_funded
    taker_pays_funded  = $_.taker_pays_funded
  }
}
if ($askRows) {
  $askRows | Format-Table -AutoSize
} else {
  "(no asks)" | Write-Host
}
