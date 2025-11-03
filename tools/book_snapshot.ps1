param(
  [string]$Issuer = "rBvZJP5WNGipMyScwFGFmDRAvcaFyn3LBY",
  [int]$Limit = 20,
  [string]$OutCsv = ""   # optional: save both books to CSV (two files)
)
$ErrorActionPreference = "Stop"

if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }
$rpc = $env:XRPL_RPC

$code160 = "434F505800000000000000000000000000000000"
$copx = @{ currency = $code160; issuer = $Issuer }

function Invoke-BookOffers {
  param($taker_gets, $taker_pays, [int]$limit = 20)
  $req = @{ method="book_offers"; params=@(@{taker_gets=$taker_gets; taker_pays=$taker_pays; limit=$limit}) }
  (Invoke-RestMethod -Method Post -Uri $rpc -ContentType 'application/json' -Body ($req | ConvertTo-Json -Depth 10)).result.offers
}

"`n== XRP/COPX (bids: pay COPX, get XRP) ==" | Write-Host
$bidOffers = Invoke-BookOffers -taker_gets @{currency="XRP"} -taker_pays $copx -limit $Limit

# For bids, quality is effectively XRP per COPX (in XRP, not drops)
$bidRows = @()
foreach ($o in ($bidOffers | ForEach-Object { $_ })) {
  $xrpPerCopx = [double]$o.quality
  $bidRows += [pscustomobject]@{
    Account      = $o.Account
    Sequence     = $o.Sequence
    xrp_per_copx = $xrpPerCopx
  }
}
if ($bidRows) { $bidRows | Format-Table -AutoSize } else { "(no bids)" | Write-Host }

"`n`n== COPX/XRP (asks: sell COPX, take XRP) ==" | Write-Host
$askOffers = Invoke-BookOffers -taker_gets $copx -taker_pays @{currency="XRP"} -limit $Limit

# For asks, compute drops_per_copx from amounts (more robust than quality math):
# drops_per_copx = taker_pays (drops) / taker_gets.value (COPX)
$askRows = @()
foreach ($o in ($askOffers | ForEach-Object { $_ })) {
  $dropsPer = $null
  if ($o.taker_pays -is [string] -and $o.taker_gets -is [hashtable]) {
    $drops     = [double]$o.taker_pays
    $gets_val  = [double]$o.taker_gets.value
    if ($gets_val -gt 0) { $dropsPer = [int]([math]::Round($drops / $gets_val, 0)) }
  } else {
    # fallback: use quality if present and already in drops-per-unit
    if ($o.PSObject.Properties.Name -contains 'quality') {
      $q = [double]$o.quality
      # if quality looks like XRP (e.g., 0.00025), convert to drops
      if ($q -lt 0.01) { $dropsPer = [int]([math]::Round($q * 1000000, 0)) } else { $dropsPer = [int]([math]::Round($q, 0)) }
    }
  }

  $askRows += [pscustomobject]@{
    Account            = $o.Account
    Sequence           = $o.Sequence
    drops_per_copx     = $dropsPer
    owner_funds        = $o.owner_funds
    taker_gets_funded  = $o.taker_gets_funded
    taker_pays_funded  = $o.taker_pays_funded
  }
}
if ($askRows) { $askRows | Format-Table -AutoSize } else { "(no asks)" | Write-Host }

# Optional CSV export
if ($OutCsv) {
  $base = (Resolve-Path ".").Path
  $bcsv = Join-Path $base ("book_bids_{0:yyyyMMdd_HHmmss}.csv" -f (Get-Date))
  $acsv = Join-Path $base ("book_asks_{0:yyyyMMdd_HHmmss}.csv" -f (Get-Date))
  if ($bidRows) { $bidRows | Export-Csv -Path $bcsv -NoTypeInformation -Encoding UTF8 }
  if ($askRows) { $askRows | Export-Csv -Path $acsv -NoTypeInformation -Encoding UTF8 }
  if ((Test-Path $bcsv) -or (Test-Path $acsv)) {
    "`nSaved:" | Write-Host
    if (Test-Path $bcsv) { " - $bcsv" | Write-Host }
    if (Test-Path $acsv) { " - $acsv" | Write-Host }
  }
}
