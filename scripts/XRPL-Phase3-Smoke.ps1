param(
    [string]$Label = "XRPL-SMOKE"
)

# ===============================================
# FUNCTION: Test-COPX-TL
# ===============================================
function Test-COPX-TL {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Address,

        [Parameter(Mandatory = $true)]
        [string]$CurrencyHex,

        [Parameter(Mandatory = $true)]
        [string]$Issuer
    )

    $payload = @{
        method = "account_lines"
        params = @(
            @{
                account = $Address
                ledger_index = "validated"
            }
        )
    }

    $resp = Invoke-RestMethod `
        -Uri "https://s.altnet.rippletest.net:51234" `
        -Method POST `
        -Body ($payload | ConvertTo-Json -Depth 10) `
        -ContentType "application/json"

    if (-not $resp.result.lines) {
        return $false
    }

    foreach ($line in $resp.result.lines) {
        if ($line.currency -eq $CurrencyHex -and
            $line.account  -eq $Issuer   -and
            [double]$line.limit -gt 0) {

            return $true
        }
    }

    return $false
}

# ===============================================
# LOAD BOOTSTRAP WALLETS
# ===============================================
$bootstrapPath = ".artifacts/data/bootstrap"
$jsonPath = Join-Path $bootstrapPath "bootstrap.json"

if (-not (Test-Path $jsonPath)) {
    Write-Host "❌ bootstrap.json missing!" -ForegroundColor Red
    exit 1
}

$bootstrap = Get-Content $jsonPath | ConvertFrom-Json
$issuer = $bootstrap.addresses.issuer
$user   = $bootstrap.addresses.user
$lp     = $bootstrap.addresses.lp

Write-Host "▶ XRPL Phase 3 Smoke Check starting (Label: $Label)..." -ForegroundColor Cyan
Write-Host "ℹ️ Loading bootstrap wallets…" -ForegroundColor Yellow
Write-Host "   Issuer: $issuer"
Write-Host "   User:   $user"
Write-Host "   LP:     $lp"

# ===============================================
# XRPL CONNECTIVITY CHECK
# ===============================================
$ping = @{
    method = "ledger"
    params = @(@{ ledger_index = "validated" })
}

try {
    Write-Host "⏱ Testing XRPL connectivity…" -ForegroundColor Yellow
    $pong = Invoke-RestMethod `
        -Uri "https://s.altnet.rippletest.net:51234" `
        -Method POST `
        -Body ($ping | ConvertTo-Json -Depth 10) `
        -ContentType "application/json"

    if ($pong.result.ledger_index -gt 0) {
        Write-Host "✅ XRPL connectivity OK" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ XRPL unreachable!" -ForegroundColor Red
    exit 1
}

# ===============================================
# CHECK TRUSTLINES
# ===============================================
Write-Host "⏱ Checking trustlines…" -ForegroundColor Yellow

$COPX_HEX = "43504F5800000000000000000000000000000000"
$COL_HEX  = "434F4C0000000000000000000000000000000000"

$u_copx = Test-COPX-TL -Address $user -CurrencyHex $COPX_HEX -Issuer $issuer
$l_copx = Test-COPX-TL -Address $lp   -CurrencyHex $COPX_HEX -Issuer $issuer

$u_col  = Test-COPX-TL -Address $user -CurrencyHex $COL_HEX  -Issuer $issuer
$l_col  = Test-COPX-TL -Address $lp   -CurrencyHex $COL_HEX  -Issuer $issuer

Write-Host ("   {0} User COPX TL" -f ($(if ($u_copx) {"✅"} else {"❌"})))
Write-Host ("   {0} User COL TL"  -f ($(if ($u_col)  {"✅"} else {"❌"})))
Write-Host ("   {0} LP COPX TL"   -f ($(if ($l_copx) {"✅"} else {"❌"})))
Write-Host ("   {0} LP COL TL"    -f ($(if ($l_col)  {"✅"} else {"❌"})))

if ($u_copx -and $l_copx) {
    Write-Host "🟢 XRPL Phase 3: COPX trustlines OK" -ForegroundColor Green
}
else {
    Write-Host "🟠 XRPL Phase 3: ISSUES DETECTED" -ForegroundColor Yellow
}

Write-Host "`n—— XRPL-Phase3 Smoke Check Completed ——"



