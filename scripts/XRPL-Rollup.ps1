param(
    [string]$Date = (Get-Date).ToString("yyyyMMdd")
)

$ErrorActionPreference = "Stop"

Write-Host "📊 XRPL Daily Ledger Rollup"
Write-Host "📅 Date: $Date"

$dir = ".artifacts/data/ledger/$Date"
$inFile = "$dir/ledger_events.json"

if (-not (Test-Path $inFile)) {
    Write-Error "Snapshot not found: $inFile"
}

# Load normalized events
$data = Get-Content $inFile -Raw | ConvertFrom-Json

# Flatten all tx into one array
$allTx = @()
$allTx += $data.issuer
$allTx += $data.user
$allTx += $data.lp

Write-Host "🔍 Loaded $($allTx.Count) TX"

# -------------------------
# Aggregates
# -------------------------
$swaps        = 0
$offers       = 0
$offerCancel  = 0
$issuedCOL    = 0
$issuedCPX    = 0
$feesTotal    = 0

foreach ($t in $allTx) {

    # fee
    if ($t.fee) {
        $feesTotal += [double]$t.fee
    }

    switch ($t.type) {

        "OfferCreate" {
            $offers += 1

            # If SELL COL
            if ($t.taker_gets -and $t.taker_gets.currency -eq "COL") {
                # treat small values as swaps / liquidity usage
                $swaps += 1
            }

            # If SELL CPX (raw hex)
            if ($t.taker_gets -and $t.taker_gets.currency -eq "4350580000000000000000000000000000000000") {
                $swaps += 1
            }
        }

        "OfferCancel" {
            $offerCancel += 1
        }

        # Issuances (Amount field, only issuer wallet)
        "Payment" {
            if ($t.account -eq $data.issuer[0].account) {
                if ($t.amount -and $t.amount.currency -eq "COL") {
                    $issuedCOL += [double]$t.amount.value
                }
                if ($t.amount -and $t.amount.currency -eq "4350580000000000000000000000000000000000") {
                    $issuedCPX += [double]$t.amount.value
                }
            }
        }
    }
}

# Ledger span
$ledgerIndices = $allTx | Select-Object -ExpandProperty sequence
$span = @{
    first = ($ledgerIndices | Measure-Object -Minimum).Minimum
    last  = ($ledgerIndices | Measure-Object -Maximum).Maximum
}

# Final rollup object
$rollup = [PSCustomObject]@{
    date     = $Date
    totals   = @{
        swaps         = $swaps
        offers        = $offers
        cancel        = $offerCancel
        issued_COL    = $issuedCOL
        issued_CPX    = $issuedCPX
        total_fees    = $feesTotal
    }
    ledger_span = $span
    wallet_breakdown = @{
        issuer = $data.issuer.Count
        user   = $data.user.Count
        lp     = $data.lp.Count
    }
}

# Save
$outFile = "$dir/ledger_rollup.json"
$rollup | ConvertTo-Json -Depth 10 | Set-Content $outFile -Encoding utf8

Write-Host "💾 Saved rollup: $outFile"
Write-Host "✅ XRPL Rollup complete." -ForegroundColor Green
