param(
    [string]$Network = "testnet",
    [int]$Limit = 50
)

$ErrorActionPreference = "Stop"

Write-Host "📡 XRPL Event Collector starting..." -ForegroundColor Cyan

# ------------------------------------------------------------
# Load bootstrap addresses
# ------------------------------------------------------------
$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
if (-not (Test-Path $bootstrapPath)) {
    Write-Error "bootstrap.json not found."
}

$bootstrap = Get-Content $bootstrapPath -Raw | ConvertFrom-Json

$issuer = $bootstrap.addresses.issuer
$user   = $bootstrap.addresses.user
$lp     = $bootstrap.addresses.lp

# ------------------------------------------------------------
# XRPL endpoint
# ------------------------------------------------------------
$endpoint = "https://s.altnet.rippletest.net:51234"

# ------------------------------------------------------------
# Function: Fetch account TX
# ------------------------------------------------------------
function Get-XRPLTx {
    param($address, $limit)

    $body = @{
        method = "account_tx"
        params = @(@{
            account = $address
            ledger_index_min = -1
            ledger_index_max = -1
            limit = $limit
        })
    } | ConvertTo-Json -Depth 10

    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -Body $body -ContentType "application/json"
    return $resp.result.transactions
}

# ------------------------------------------------------------
# Fetch all three accounts
# ------------------------------------------------------------
Write-Host "🔎 Fetching issuer tx..."
$issuerTx = Get-XRPLTx -address $issuer -limit $Limit

Write-Host "🔎 Fetching user tx..."
$userTx = Get-XRPLTx -address $user -limit $Limit

Write-Host "🔎 Fetching LP tx..."
$lpTx = Get-XRPLTx -address $lp -limit $Limit

# ------------------------------------------------------------
# Normalize transactions
# ------------------------------------------------------------
function Normalize-Tx {
    param($tx)

    $t = $tx.tx
    $meta = $tx.meta

    return [PSCustomObject]@{
        hash        = $t.hash
        type        = $t.TransactionType
        account     = $t.Account
        fee         = $t.Fee
        sequence    = $t.Sequence
        date        = $t.date
        validated   = $tx.validated
        taker_gets  = $t.TakerGets
        taker_pays  = $t.TakerPays
        amount      = $t.Amount
        offer_data  = $meta.AffectedNodes
    }
}

$norm = @{
    issuer = $issuerTx | ForEach-Object { Normalize-Tx $_ }
    user   = $userTx   | ForEach-Object { Normalize-Tx $_ }
    lp     = $lpTx     | ForEach-Object { Normalize-Tx $_ }
}

# ------------------------------------------------------------
# Save snapshot
# ------------------------------------------------------------
$today = (Get-Date).ToString("yyyyMMdd")
$dir = ".artifacts/data/ledger/$today"

if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir | Out-Null
}

$outFile = "$dir/ledger_events.json"
$norm | ConvertTo-Json -Depth 20 | Set-Content $outFile -Encoding utf8

Write-Host "💾 Saved ledger snapshot: $outFile"
Write-Host "✅ XRPL Event Collector complete." -ForegroundColor Green
