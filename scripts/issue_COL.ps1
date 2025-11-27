param(
    [Parameter(Mandatory=$true)]
    [string]$IssuerSeed,

    [Parameter(Mandatory=$true)]
    [string]$IssuerAddress
)

Write-Host "🔵 Issuing COL token..." -ForegroundColor Cyan

$currency = "COL00000000000000000000000000000000000000"

# TrustSet from issuer to itself initializes the currency on XRPL
$tx = @{
    "TransactionType" = "TrustSet"
    "Account" = $IssuerAddress
    "LimitAmount" = @{
        "currency" = $currency
        "issuer"   = $IssuerAddress
        "value"    = "1000000000000000"
    }
    "Flags" = 131072
}

$payload = @{
    method = "submit"
    params = @(
        @{
            secret  = $IssuerSeed
            tx_json = $tx
        }
    )
}

Write-Host "Submitting COL issuance TX..." -ForegroundColor Yellow

$response = Invoke-RestMethod `
    -Uri "https://s.altnet.rippletest.net:51234" `
    -Method Post `
    -Body ($payload | ConvertTo-Json -Depth 10) `
    -ContentType "application/json"

$response | ConvertTo-Json -Depth 10

Write-Host "🟢 COL Token initialized on XRPL Testnet" -ForegroundColor Green
