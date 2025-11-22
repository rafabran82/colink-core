param(
    [Parameter(Mandatory=$true)]
    [string] $Address
)

Write-Host "🚰 Requesting Testnet XRP for $Address ..." -ForegroundColor Cyan

$body = @{
    destination = $Address
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod `
        -Uri "https://faucet.altnet.rippletest.net/accounts" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body

    Write-Host "🟢 Faucet Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5 | Write-Output
}
catch {
    Write-Host "❌ Error requesting Testnet XRP" -ForegroundColor Red
    Write-Host $_
}
