# scripts/Seed-Pools-5B-Validate.ps1
$ErrorActionPreference = "Stop"
Write-Host "🧪 Step 5B — Validating Orderbook Health" -ForegroundColor Cyan

$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
$orderbookPath = ".artifacts/data/bootstrap/orderbooks_step5.json"

$bootstrap = Get-Content $bootstrapPath -Raw | ConvertFrom-Json
$data      = Get-Content $orderbookPath -Raw | ConvertFrom-Json

$user = $bootstrap.addresses.user
$lp   = $bootstrap.addresses.lp

function Test-Pool {
    param($label, $offers, $user, $lp)

    Write-Host "`n=== Checking $label ==="

    if ($offers.Count -lt 2) {
        Write-Host "❌ Missing offers (expected 2)" -ForegroundColor Red
        return $false
    }

    $accounts = $offers.Account

    if (-not ($accounts -contains $user)) {
        Write-Host "❌ User offer missing" -ForegroundColor Red
        return $false
    }
    if (-not ($accounts -contains $lp)) {
        Write-Host "❌ LP offer missing" -ForegroundColor Red
        return $false
    }

    Write-Host "✔️ Owners OK (User + LP)" -ForegroundColor Green

    foreach ($o in $offers) {
        if ($o.TakerGets.value -ne "500000") {
            Write-Host "❌ Wrong TakerGets: $($o.TakerGets.value)" -ForegroundColor Red
            return $false
        }
        if ([double]$o.TakerPays -ne 50000000) {
            Write-Host "❌ Wrong TakerPays: $($o.TakerPays)" -ForegroundColor Red
            return $false
        }
    }

    Write-Host "✔️ Amounts OK (500k → 50 XRP)" -ForegroundColor Green
    return $true
}

$ok1 = Test-Pool "COL/XRP" $data.COL_XRP $user $lp
$ok2 = Test-Pool "CPX/XRP" $data.CPX_XRP $user $lp

if ($ok1 -and $ok2) {
    Write-Host "`n🟢 ALL POOLS HEALTHY — COLINK liquidity seeded successfully!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Pool validation failed." -ForegroundColor Red
}
