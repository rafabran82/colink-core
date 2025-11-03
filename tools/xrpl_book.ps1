function Invoke-BookOffers {
  param($taker_gets, $taker_pays, [int]$limit = 20)
  $req = @{ method="book_offers"; params=@(@{taker_gets=$taker_gets; taker_pays=$taker_pays; limit=$limit}) }
  (Invoke-RestMethod -Method Post -Uri $env:XRPL_RPC -ContentType 'application/json' -Body ($req | ConvertTo-Json -Depth 10)).result.offers
}
