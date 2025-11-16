# scripts/Seed-Pools-Summary.ps1
$ErrorActionPreference = "Stop"

Write-Host "🟦 COLINK – Final Pool Seeding Summary" -ForegroundColor Cyan

# ---------------------------
# Load bootstrap + orderbooks
# ---------------------------
$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
$orderbookPath = ".artifacts/data/bootstrap/orderbooks_step5.json"

if (-not (Test-Path $bootstrapPath)) { Write-Error "bootstrap.json missing" }
if (-not (Test-Path $orderbookPath)) { Write-Error "orderbooks_step5.json missing" }

$bootstrap = Get-Content $bootstrapPath -Raw | ConvertFrom-Json
$data      = Get-Content $orderbookPath -Raw | ConvertFrom-Json

$issuer = $bootstrap.addresses.issuer
$user   = $bootstrap.addresses.user
$lp     = $bootstrap.addresses.lp

Write-Host "`n📌 ADDRESSES"
Write-Host "  Issuer: $issuer"
Write-Host "  User:   $user"
Write-Host "  LP:     $lp"

# ---------------------------
# Check orderbooks
# ---------------------------
function Print-Pool {
    param($label, $offers)

    Write-Host "`n📘 $label Orderbook"
    foreach ($o in $offers) {
        $acc = $o.Account
        $tg  = $o.TakerGets.value
        $tp  = $o.TakerPays
        Write-Host " - $acc | Gets=$tg Pays=$tp"
    }
}

Print-Pool "COL/XRP" $data.COL_XRP
Print-Pool "CPX/XRP" $data.CPX_XRP

# ---------------------------
# Quick health check
# ---------------------------
function Test-Pool {
    param($offers, $user, $lp)

    $accounts = $offers.Account
    if (-not ($accounts -contains $user)) { return $false }
    if (-not ($accounts -contains $lp)) { return $false }

    foreach ($o in $offers) {
        if ($o.TakerGets.value -ne "500000") { return $false }
        if ([double]$o.TakerPays -ne 50000000) { return $false }
    }
    return $true
}

$ok1 = Test-Pool $data.COL_XRP $user $lp
$ok2 = Test-Pool $data.CPX_XRP $user $lp

# ---------------------------
# FINAL REPORT
# ---------------------------
Write-Host "`n==============================="
if ($ok1 -and $ok2) {
    Write-Host "🟢 FINAL RESULT: ALL POOLS HEALTHY" -ForegroundColor Green
    Write-Host "     COLINK Liquidity Seeding Complete ✔️"
} else {
    Write-Host "❌ FINAL RESULT: Pool Health Issues" -ForegroundColor Red
}
Write-Host "==============================="
