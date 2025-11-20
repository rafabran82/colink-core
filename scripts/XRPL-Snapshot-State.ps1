param(
    [string]$Label = "XRPL-SNAPSHOT"
)

Write-Host "▶ XRPL → SIM State Snapshot starting (Label: $Label)..." -ForegroundColor Cyan

# Load bootstrap
$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
if (-not (Test-Path $bootstrapPath)) {
    Write-Host "❌ bootstrap.json missing!" -ForegroundColor Red
    exit 1
}

$boot = Get-Content $bootstrapPath | ConvertFrom-Json
$issuer = $boot.addresses.issuer
$user   = $boot.addresses.user
$lp     = $boot.addresses.lp

# XRPL endpoint
$rpc = "https://s.altnet.rippletest.net:51234"

function Get-XRPL {
    param($Body)
    return Invoke-RestMethod -Uri $rpc -Method POST -Body ($Body | ConvertTo-Json -Depth 10) -ContentType "application/json"
}

function Get-Account {
    param([string]$Acct)

    $payload = @{
        method = "account_info"
        params = @(@{ account = $Acct; ledger_index = "validated" })
    }

    return Get-XRPL $payload
}

function Get-Lines {
    param([string]$Acct)

    $payload = @{
        method = "account_lines"
        params = @(@{ account = $Acct; ledger_index = "validated" })
    }

    return Get-XRPL $payload
}

Write-Host "⏱ Fetching account states…" -ForegroundColor Yellow

$state = [ordered]@{
    timestamp   = (Get-Date).ToString("o")
    ledger      = (Get-XRPL @{method="ledger"; params=@(@{ledger_index="validated"})}).result.ledger_index
    accounts    = @{
        issuer = @{
            address      = $issuer
            account_info = (Get-Account $issuer).result.account_data
            trustlines   = (Get-Lines  $issuer).result.lines
        }
        user = @{
            address      = $user
            account_info = (Get-Account $user).result.account_data
            trustlines   = (Get-Lines  $user).result.lines
        }
        lp = @{
            address      = $lp
            account_info = (Get-Account $lp).result.account_data
            trustlines   = (Get-Lines  $lp).result.lines
        }
    }
}

$outDir = ".artifacts/sim"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory $outDir | Out-Null }

$outFile = "$outDir/xrpl_state.json"
$state | ConvertTo-Json -Depth 20 | Set-Content -Path $outFile -Encoding utf8

Write-Host ""
Write-Host "🟢 XRPL → SIM Snapshot Complete" -ForegroundColor Green
Write-Host "📦 Output: $outFile"
Write-Host ""

Write-Host "—— XRPL-Snapshot-State Completed ——"
