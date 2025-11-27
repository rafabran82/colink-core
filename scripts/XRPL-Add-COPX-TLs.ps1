param(
    [string]$Label = "ADD-COPX-TRUSTLINES"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "▶ Adding missing COPX trustlines (Label: $Label)..." -ForegroundColor Cyan

try {
    $root = Split-Path $PSScriptRoot -Parent
    Set-Location $root

    # Load bootstrap wallets
    $bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
    if (-not (Test-Path $bootstrapPath)) {
        Write-Host "❌ Missing bootstrap.json" -ForegroundColor Red
        return
    }

    $bootstrap = Get-Content $bootstrapPath | ConvertFrom-Json

    $issuerSeed = $bootstrap.issuer
    $userSeed   = $bootstrap.user
    $lpSeed     = $bootstrap.lp

    $issuerAddr = $bootstrap.addresses.issuer
    $userAddr   = $bootstrap.addresses.user
    $lpAddr     = $bootstrap.addresses.lp

    Write-Host "ℹ️ COPX TL Targets:"
    Write-Host "   User: $userAddr"
    Write-Host "   LP:   $lpAddr"
    Write-Host ""

    # Python trustline tool
    $tlScript = Join-Path $PSScriptRoot "xrpl_add_trustline.py"
    if (-not (Test-Path $tlScript)) {
        Write-Host "❌ Missing xrpl_add_trustline.py" -ForegroundColor Red
        return
    }

    $okUser = $true
    $okLp   = $true

    # User COPX TL
    Write-Host "➡️ Adding COPX TL for USER…" -ForegroundColor Cyan
    & python $tlScript `
        --seed "$userSeed" --account "$userAddr" `
        --issuer "$issuerAddr" `
        --currency "43504F5800000000000000000000000000000000" `
        --value "1000000000"  

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ User COPX TL creation failed (exit code $LASTEXITCODE)" -ForegroundColor Red
        $okUser = $false
    }
    else {
        Write-Host "✅ User COPX TL command exited cleanly" -ForegroundColor Green
    }

    # LP COPX TL
    Write-Host "➡️ Adding COPX TL for LP…" -ForegroundColor Cyan
    & python $tlScript `
        --seed "$lpSeed" --account "$lpAddr" `
        --issuer "$issuerAddr" `
        --currency "43504F5800000000000000000000000000000000" `
        --value "1000000000"  

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ LP COPX TL creation failed (exit code $LASTEXITCODE)" -ForegroundColor Red
        $okLp = $false
    }
    else {
        Write-Host "✅ LP COPX TL command exited cleanly" -ForegroundColor Green
    }

    Write-Host ""

    if ($okUser -and $okLp) {
        Write-Host "🟢 COPX trustline patch completed successfully for USER and LP" -ForegroundColor Green
    }
    else {
        Write-Host "🟠 COPX trustline patch had issues (see messages above)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Exception: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🟠 COPX TL Script FAILED" -ForegroundColor Yellow
}
finally {
    Write-Host ""
    Write-Host "—— XRPL-Add-COPX-TLs Completed ——" -ForegroundColor DarkGray
}







