param(
    [string]$Label = "XRPL-ADD-COL-TLs"
)

Write-Host ""
Write-Host "▶ Adding missing COL trustlines (Label: $Label)..." -ForegroundColor Cyan

# Load bootstrap
$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
if (-not (Test-Path $bootstrapPath)) {
    Write-Host "❌ bootstrap.json missing!" -ForegroundColor Red
    exit 1
}

$boot = Get-Content $bootstrapPath | ConvertFrom-Json

$issuer_seed = $boot.issuer
$user_seed   = $boot.user
$lp_seed     = $boot.lp

$issuer_addr = $boot.addresses.issuer
$user_addr   = $boot.addresses.user
$lp_addr     = $boot.addresses.lp

$scriptCol = Join-Path $PSScriptRoot "xrpl_add_trustline_col.py"
if (-not (Test-Path $scriptCol)) {
    Write-Host "❌ Missing Python trustline script: xrpl_add_trustline_col.py" -ForegroundColor Red
    exit 1
}

$COL_HEX = "434F4C0000000000000000000000000000000000"

Write-Host ""
Write-Host "ℹ️ COL TL Targets:" -ForegroundColor Yellow
Write-Host "   User: $user_addr"
Write-Host "   LP:   $lp_addr"
Write-Host ""

# USER
Write-Host "➡️ Adding COL TL for USER…" -ForegroundColor Yellow
& python $scriptCol $user_seed $issuer_addr $COL_HEX 2>&1 | Write-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ User COL TL failed (exit code $LASTEXITCODE)" -ForegroundColor Red
} else {
    Write-Host "✅ User COL TL command exited cleanly" -ForegroundColor Green
}

Write-Host ""
# LP
Write-Host "➡️ Adding COL TL for LP…" -ForegroundColor Yellow
& python $scriptCol $lp_seed $issuer_addr $COL_HEX 2>&1 | Write-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ LP COL TL failed (exit code $LASTEXITCODE)" -ForegroundColor Red
} else {
    Write-Host "✅ LP COL TL command exited cleanly" -ForegroundColor Green
}

Write-Host ""
Write-Host "🟢 COL trustline patch completed (USER + LP)" -ForegroundColor Green
Write-Host ""
Write-Host "—— XRPL-Add-COL-TLs Completed ——"
