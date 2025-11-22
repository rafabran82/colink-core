param(
    [Parameter(Mandatory=$true)]
    [string]$IssuerAddress,

    [Parameter(Mandatory=$true)]
    [string]$UserAddress,
    [Parameter(Mandatory=$true)]
    [string]$UserSeed,

    [Parameter(Mandatory=$true)]
    [string]$LPAddress,
    [Parameter(Mandatory=$true)]
    [string]$LPSeed
)

$RPC = "https://testnet.xrpl-labs.com"
$currency = "COL00000000000000000000000000000000000000"

Write-Host "🔵 Setting COL trustlines for USER + LP (XRPL-Labs Testnet)..." -ForegroundColor Cyan

function Submit-TrustSet {
    param(
        [string]$Account,
        [string]$Seed
    )

    $tx = @{
        TransactionType = "TrustSet"
        Account         = $Account
        LimitAmount     = @{
            currency = $currency
            issuer   = $IssuerAddress
            value    = "100000000000"
        }
        Flags = 131072
    }

    $payload = @{
        method = "submit"
        params = @(
            @{
                secret  = $Seed
                tx_json = $tx
            }
        )
    }

    try {
        $response = Invoke-RestMethod `
            -Uri $RPC `
            -Method Post `
            -Body ($payload | ConvertTo-Json -Depth 10) `
            -ContentType "application/json"

        return $response
    }
    catch {
        return @{ error = $_.Exception.Message }
    }
}

Write-Host "➡️ Setting USER trustline..."
$userResult = Submit-TrustSet -Account $UserAddress -Seed $UserSeed

Write-Host "➡️ Setting LP trustline..."
$lpResult = Submit-TrustSet -Account $LPAddress -Seed $LPSeed

Write-Host ""
Write-Host "============================"
Write-Host "   TRUSTLINE SUMMARY"
Write-Host "============================"

if ($userResult.error) {
    Write-Host "❌ USER trustline failed: $($userResult.error)" -ForegroundColor Red
} else {
    Write-Host "🟢 USER trustline OK" -ForegroundColor Green
}

if ($lpResult.error) {
    Write-Host "❌ LP trustline failed: $($lpResult.error)" -ForegroundColor Red
} else {
    Write-Host "🟢 LP trustline OK" -ForegroundColor Green
}

Write-Host "============================"
Write-Host "   DONE"
Write-Host "============================"
