param(
    [Parameter(Mandatory=$true)]
    [string]$Address
)

$uri = "https://faucet.altnet.rippletest.net/accounts"  # fixed endpoint
$body = @{ destination = $Address } | ConvertTo-Json

try {
    Write-Host "🚰 Funding wallet via Testnet faucet..." -ForegroundColor Cyan
    Write-Host "   Address: $Address"
    $resp = Invoke-RestMethod -Method Post -Uri $uri -Body $body -ContentType "application/json"
    Write-Host "💧 Faucet response:" -ForegroundColor Yellow
    $resp | ConvertTo-Json -Depth 10
    Write-Host "🟢 Wallet funded successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Faucet funding failed: $($_.Exception.Message)" -ForegroundColor Red
}
