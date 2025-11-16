param(
    [switch]$Execute,
    [string]$Network = "testnet",
    [int]$Amount = 10
)

$ErrorActionPreference = "Stop"

Write-Host "🔁 COLINK Real Swap Executor (Testnet)" -ForegroundColor Cyan
Write-Host "Pool: COL_XRP"
Write-Host "Amount In: $Amount COL"

# --------------------------------------------
# Load bootstrap.json
# --------------------------------------------
$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
if (-not (Test-Path $bootstrapPath)) {
    Write-Error "bootstrap.json not found."
}

$bootstrap = Get-Content $bootstrapPath -Raw | ConvertFrom-Json

$issuer_seed = $bootstrap.issuer
$user_seed   = $bootstrap.user
$lp_seed     = $bootstrap.lp

$issuer_addr = $bootstrap.addresses.issuer
$user_addr   = $bootstrap.addresses.user
$lp_addr     = $bootstrap.addresses.lp

# --------------------------------------------
# Build tiny OfferTake Python executor
# --------------------------------------------
$py = @"
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import autofill, sign, submit_and_wait
import json, sys

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

user = Wallet.from_seed("$user_seed")

amount_in = $Amount
value_in = str(amount_in)
taker_pays = "1"  # placeholder, will be ignored by XRPL for buy offers

# We create a BUY order: pay COL, receive XRP
tx = OfferCreate(
    account=user.classic_address,
    taker_gets={
        "currency": "COL",
        "issuer": "$issuer_addr",
        "value": value_in
    },
    taker_pays="1"   # buy XRP for COL
)

prepared = autofill(tx, client)
signed = sign(prepared, user)
resp = submit_and_wait(signed, client)

print(json.dumps(resp.result))
"@

# --------------------------------------------
# Execution toggle
# --------------------------------------------
if (-not $Execute) {
    Write-Host "🧪 Dry-run only. Use -Execute to submit real transaction." -ForegroundColor Yellow
    exit
}

Write-Host "🚀 Executing real on-ledger swap (Testnet)..."

$out = $py | python
Write-Host $out

# Save ledger result
Set-Content ".artifacts/data/bootstrap/swap_result.json" -Encoding utf8 -Value $out

Write-Host "💾 Saved swap result to swap_result.json" -ForegroundColor Green
Write-Host "✅ Swap execution complete" -ForegroundColor Green
