param(
    [Parameter(Mandatory=$true)][string]$IssuerSeed,
    [Parameter(Mandatory=$true)][string]$DestAddress,
    [Parameter(Mandatory=$true)][long]$Amount
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "▶ Issuing COPX to $DestAddress (Amount: $Amount)..." -ForegroundColor Cyan

$py = Join-Path $PSScriptRoot "xrpl_issue_token.py"
if (-not (Test-Path $py)) {
    Write-Host "❌ Missing xrpl_issue_token.py" -ForegroundColor Red
    exit 1
}

& python $py `
    --seed "$IssuerSeed" `
    --destination "$DestAddress" `
    --currency "COPX" `
    --amount "$Amount" `
    --rpc "https://s.altnet.rippletest.net:51234" `
    2>&1 | ForEach-Object { Write-Host "   $_" }

Write-Host ""
Write-Host "🟢 COPX issued: $Amount to $DestAddress" -ForegroundColor Green
Write-Host "—— XRPL-COPX-Issue Completed ——"
