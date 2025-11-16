param(
    [string]$Date = (Get-Date).ToString("yyyyMMdd")
)

$rollPath = ".artifacts/data/ledger/$Date/ledger_rollup.json"
if (-not (Test-Path $rollPath)) {
    Write-Error "Rollup file not found: $rollPath"
    exit 1
}

$roll = Get-Content $rollPath -Raw | ConvertFrom-Json

# Build compact dashboard metrics
$metrics = [PSCustomObject]@{
    date            = $Date
    total_tx        = $roll.count
    unique_accounts = ($roll.accounts | Get-Unique).Count
    swap_tx         = $roll.types.swap
    offer_create    = $roll.types.offercreate
    payment_tx      = $roll.types.payment
    min_ledger      = $roll.ledger.min
    max_ledger      = $roll.ledger.max
    first_tx_hash   = $roll.first.hash
    last_tx_hash    = $roll.last.hash
}

$metrics | ConvertTo-Json -Depth 10
