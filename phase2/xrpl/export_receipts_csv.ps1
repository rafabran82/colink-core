param(
  [string]$Folder = "$(Join-Path $PSScriptRoot 'otc_receipts')",
  [string]$OutCsv = "$(Join-Path $PSScriptRoot 'otc_receipts_export.csv')"
)
if (!(Test-Path $Folder)) {
  Write-Error "Receipts folder not found: $Folder"
  exit 1
}

$rows = New-Object System.Collections.Generic.List[object]
Get-ChildItem -Path $Folder -Filter 'otc-*.json' | Sort-Object Name | ForEach-Object {
  $rec = Get-Content $_.FullName | ConvertFrom-Json
  $qty   = [decimal]$rec.params.qty_copx
  $price = [double]$rec.params.price_xrp
  $slip  = [double]$rec.params.slippage
  $cap   = [int64]$rec.params.cap_drops

  $makerBefore = [int64]$rec.before.maker.xrp_drops
  $makerAfter  = [int64]$rec.after.maker.xrp_drops
  $takerBefore = [int64]$rec.before.taker.xrp_drops
  $takerAfter  = [int64]$rec.after.taker.xrp_drops

  $makerDelta = $makerAfter - $makerBefore
  $takerDelta = $takerAfter - $takerBefore

  $rows.Add([pscustomobject]@{
    file                = $_.Name
    ts_iso              = $rec.ts_iso
    qty_copx            = $qty
    price_xrp           = $price
    slippage            = $slip
    cap_drops           = $cap
    step1_engine        = $rec.step1.engine_result
    step1_hash          = $rec.step1.hash
    step2_engine        = $rec.step2.engine_result
    step2_hash          = $rec.step2.hash
    maker_delta_drops   = $makerDelta
    taker_delta_drops   = $takerDelta
  })
}

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv
Write-Host "Wrote CSV:" -ForegroundColor Green
Write-Host $OutCsv
