param(
    [switch]$Execute,
    [string]$Network = "testnet"
)

$ErrorActionPreference = "Stop"

Write-Host "🏦 COLINK Pool Seeding – Step 4 (OfferCreate Execution)" -ForegroundColor Cyan

# ------------------------------------------------------------
# Load bootstrap.json
# ------------------------------------------------------------
$bootstrapPath = ".artifacts/data/bootstrap/bootstrap.json"
if (-not (Test-Path $bootstrapPath)) {
    Write-Error "bootstrap.json not found at $bootstrapPath"
}

$bootstrap = Get-Content $bootstrapPath -Raw | ConvertFrom-Json

$issuer_seed = $bootstrap.issuer
$user_seed   = $bootstrap.user
$lp_seed     = $bootstrap.lp

$issuer_addr = $bootstrap.addresses.issuer
$user_addr   = $bootstrap.addresses.user
$lp_addr     = $bootstrap.addresses.lp

Write-Host "📦 Loaded bootstrap:"
Write-Host "  Issuer: $issuer_addr"
Write-Host "  User:   $user_addr"
Write-Host "  LP:     $lp_addr"

# ------------------------------------------------------------
# Python logic for OfferCreate
# ------------------------------------------------------------
$py = @"
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait
import json, sys

issuer_seed = "$issuer_seed"
user_seed   = "$user_seed"
lp_seed     = "$lp_seed"

issuer = Wallet.from_seed(issuer_seed)
user   = Wallet.from_seed(user_seed)
lp     = Wallet.from_seed(lp_seed)

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# ------------------------------------------------------------
# Helper to make IC amounts
# ------------------------------------------------------------
def ic(currency, issuer, value):
    return IssuedCurrencyAmount(
        currency=currency,
        issuer=issuer,
        value=str(value)
    )

# ------------------------------------------------------------
# Build OfferCreate transactions
# ------------------------------------------------------------
offers = []

# USER offers
offers.append({
    "wallet": "user",
    "tx": OfferCreate(
        account=user.classic_address,
        taker_gets=ic("COL", issuer.classic_address, 500000),
        taker_pays="50000000"  # 50 XRP (drops)
    )
})
offers.append({
    "wallet": "user",
    "tx": OfferCreate(
        account=user.classic_address,
        taker_gets=ic("4350580000000000000000000000000000000000",
                      issuer.classic_address, 500000),
        taker_pays="50000000"
    )
})

# LP offers
offers.append({
    "wallet": "lp",
    "tx": OfferCreate(
        account=lp.classic_address,
        taker_gets=ic("COL", issuer.classic_address, 500000),
        taker_pays="50000000"
    )
})
offers.append({
    "wallet": "lp",
    "tx": OfferCreate(
        account=lp.classic_address,
        taker_gets=ic("4350580000000000000000000000000000000000",
                      issuer.classic_address, 500000),
        taker_pays="50000000"
    )
})

# ------------------------------------------------------------
# Print summary
# ------------------------------------------------------------
print("=== OFFERS TO SUBMIT (DRY RUN) ===")
for o in offers:
    print(o["wallet"], "→", o["tx"].to_xrpl())

# ------------------------------------------------------------
# Execute if requested
# ------------------------------------------------------------
if "$Execute" == "True":
    print("=== EXECUTING OFFERS ===")
    for o in offers:
        wallet = user if o["wallet"] == "user" else lp
        prepared = autofill(o["tx"], client)
        signed = sign(prepared, wallet)
        resp = submit_and_wait(signed, client)
        print(json.dumps(resp.result, indent=2))
else:
    print("=== DRY RUN ONLY ===")

"@

Write-Host "🚀 Running OfferCreate plan..."
$out = $py | python
Write-Host $out

if ($out -match "Traceback") {
    Write-Error "❌ Python error detected."
}

Write-Host "✅ Step 4 Complete — OfferCreate Ready" -ForegroundColor Green
