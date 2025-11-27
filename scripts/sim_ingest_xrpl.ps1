param(
    [string]$Label = "SIM-INGEST-XRPL"
)

Write-Host "▶ SIM Ingest XRPL Snapshot (Label: $Label)..." -ForegroundColor Cyan

$src = ".artifacts/sim/xrpl_state.json"
if (-not (Test-Path $src)) {
    Write-Host "❌ Missing XRPL state: $src" -ForegroundColor Red
    exit 1
}

$raw = Get-Content $src | ConvertFrom-Json

$issuer = $raw.accounts.issuer
$user   = $raw.accounts.user
$lp     = $raw.accounts.lp

function Get-IssuedBalance {
    param($lines, $currencyHex, $issuer)

    foreach ($l in $lines) {
        if ($l.currency -eq $currencyHex -and $l.account -eq $issuer) {
            return $l.balance
        }
    }
    return "0"
}

$COPX = "434F505800000000000000000000000000000000"
$COL  = "434F4C0000000000000000000000000000000000"

$sim = [ordered]@{
    timestamp = $raw.timestamp
    ledger    = $raw.ledger
    accounts  = @{
        issuer = @{
            address = $issuer.address
            XRP     = $issuer.account_info.Balance
        }
        user = @{
            address = $user.address
            XRP     = $user.account_info.Balance
            COPX    = Get-IssuedBalance $user.trustlines $COPX $issuer.address
            COL     = Get-IssuedBalance $user.trustlines $COL  $issuer.address
        }
        lp = @{
            address = $lp.address
            XRP     = $lp.account_info.Balance
            COPX    = Get-IssuedBalance $lp.trustlines $COPX $issuer.address
            COL     = Get-IssuedBalance $lp.trustlines $COL  $issuer.address
        }
    }
}

$out = ".artifacts/sim/sim_state.json"
$sim | ConvertTo-Json -Depth 10 | Set-Content $out -Encoding utf8

Write-Host ""
Write-Host "🟢 SIM ingest ready" -ForegroundColor Green
Write-Host "📦 Output: $out"
Write-Host ""
Write-Host "—— SIM Ingest XRPL Completed ——"
