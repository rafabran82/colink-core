param(
    [string]$Date
)

$rollPath = ".artifacts/data/ledger/$Date/ledger_rollup.json"

if (-not (Test-Path $rollPath)) {
    Write-Error "Rollup file not found: $rollPath"
    exit 1
}

$roll = Get-Content $rollPath -Raw | ConvertFrom-Json

# Build intelligence metrics block
$metrics = [PSCustomObject]@{
    date             = $roll.date
    total_tx         = ($roll.totals.swaps + $roll.totals.offers + $roll.totals.cancel)
    swaps            = $roll.totals.swaps
    offers           = $roll.totals.offers
    cancels          = $roll.totals.cancel
    issued_COL       = $roll.totals.issued_COL
    issued_CPX       = $roll.totals.issued_CPX
    fees_total       = $roll.totals.total_fees
    accounts_lp      = $roll.wallet_breakdown.lp
    accounts_issuer  = $roll.wallet_breakdown.issuer
    accounts_user    = $roll.wallet_breakdown.user
    ledger_first     = $roll.ledger_span.first
    ledger_last      = $roll.ledger_span.last
}

$metrics | ConvertTo-Json -Depth 10
