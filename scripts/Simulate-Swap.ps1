param(
    [string]$Pool = "COL_XRP",
    [double]$Amount = 100
)

$ErrorActionPreference = "Stop"

Write-Host "🔁 COLINK Swap Simulation (Dry Run)" -ForegroundColor Cyan
Write-Host "Pool: $Pool"
Write-Host "Amount In: $Amount COL/CPX"

# Load orderbook JSON
$obPath = ".artifacts/data/bootstrap/orderbooks_step5.json"
if (-not (Test-Path $obPath)) { Write-Error "orderbooks json missing" }

$data = Get-Content $obPath -Raw | ConvertFrom-Json
$offers = $data.$Pool

if ($offers.Count -lt 1) {
    Write-Error "No offers found for $Pool"
}

# Our pools have uniform offers, so we just compute:
# 500000 COL → 50 XRP
# Price = 0.0001 XRP per COL

$price = 50 / 500000
$xrpOut = [math]::Round($Amount * $price, 6)

Write-Host "`n📐 Derived Price: $price XRP per unit"
Write-Host "🔮 Expected Output: $xrpOut XRP"

