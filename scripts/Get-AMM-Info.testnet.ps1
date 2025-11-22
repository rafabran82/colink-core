param(
    [Parameter(Mandatory = $true)]
    [string]$Currency,

    [Parameter(Mandatory = $true)]
    [string]$Issuer,

    [string]$RpcUrl = "https://s.altnet.rippletest.net:51234"
)

Write-Host ""
Write-Host "🔍 Get-AMM-Info.testnet" -ForegroundColor Cyan
Write-Host "   Asset pair : $Currency/XRP" -ForegroundColor Cyan
Write-Host "   Issuer     : $Issuer" -ForegroundColor Cyan
Write-Host "   RPC URL    : $RpcUrl" -ForegroundColor Cyan
Write-Host ""

# Build XRPL amm_info request
$payload = @{
    method = "amm_info"
    params = @(
        @{
            asset  = @{
                currency = $Currency
                issuer   = $Issuer
            }
            asset2 = @{
                currency = "XRP"
            }
        }
    )
}

$bodyJson = $payload | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri $RpcUrl -Method Post -Body $bodyJson -ContentType "application/json"

    if (-not $response) {
        Write-Host "❌ No response from XRPL server." -ForegroundColor Red
        Write-Host "🔴 AMM-INFO: FAILED (no response)" -ForegroundColor Red
        exit 1
    }

    $result = $response.result

    if ($null -eq $result) {
        Write-Host "❌ Unexpected response format:" -ForegroundColor Red
        $response | ConvertTo-Json -Depth 10
        Write-Host "🔴 AMM-INFO: FAILED (missing result)" -ForegroundColor Red
        exit 1
    }

    if ($result.error) {
        Write-Host "❌ XRPL error:" -ForegroundColor Red
        Write-Host "   error      : $($result.error)" -ForegroundColor Red
        Write-Host "   error_code : $($result.error_code)" -ForegroundColor Red
        Write-Host "   error_msg  : $($result.error_message)" -ForegroundColor Red
        Write-Host "🔴 AMM-INFO: FAILED (XRPL error)" -ForegroundColor Red
        exit 1
    }

    $amm = $result.amm

    if ($null -eq $amm) {
        Write-Host "⚠️ No AMM object found in response. Full result:" -ForegroundColor Yellow
        $result | ConvertTo-Json -Depth 10
        Write-Host "🟡 AMM-INFO: WARNING (no amm object)" -ForegroundColor Yellow
        exit 0
    }

    Write-Host "✅ AMM found for $Currency/XRP:" -ForegroundColor Green
    Write-Host ""

    if ($amm.account) {
        Write-Host "   AMM Account : $($amm.account)"
    }
    if ($amm.lp_token) {
        Write-Host "   LP Token    : $($amm.lp_token.currency) / Issuer: $($amm.lp_token.issuer)"
    }
    if ($amm.trading_fee -ne $null) {
        Write-Host "   Trading fee : $($amm.trading_fee)"
    }

    if ($amm.amount) {
        Write-Host ""
        Write-Host "   🔹 Pool Leg 1 (Asset) :" -ForegroundColor Cyan
        $amm.amount | ConvertTo-Json -Depth 10
    }
    if ($amm.amount2) {
        Write-Host ""
        Write-Host "   🔹 Pool Leg 2 (Asset2):" -ForegroundColor Cyan
        $amm.amount2 | ConvertTo-Json -Depth 10
    }

    if ($amm.vote_slots) {
        Write-Host ""
        Write-Host "   🔹 Vote Slots:" -ForegroundColor Cyan
        $amm.vote_slots | ConvertTo-Json -Depth 10
    }

    Write-Host ""
    Write-Host "🟢 AMM-INFO: success for $Currency/XRP" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "❌ Exception while calling XRPL:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "🔴 AMM-INFO: FAILED (exception)" -ForegroundColor Red
    exit 1
}
