param(
    [switch]$Execute,
    [string]$Network = "testnet"
)

$ErrorActionPreference = "Stop"

Write-Host "🌱 COLINK Pool Seeding (Step 1: Validation Only)" -ForegroundColor Cyan

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
# Run a tiny Python check to validate wallet loading + client
# ------------------------------------------------------------
$py = @"
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
import json, sys

issuer_seed = "$issuer_seed"
user_seed   = "$user_seed"
lp_seed     = "$lp_seed"

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

try:
    issuer = Wallet.from_seed(issuer_seed)
    user   = Wallet.from_seed(user_seed)
    lp     = Wallet.from_seed(lp_seed)
except Exception as e:
    print("ERROR: Wallet load failed:", e)
    sys.exit(1)

print("OK: Wallets loaded")
print("Issuer:", issuer.classic_address)
print("User:  ", user.classic_address)
print("LP:    ", lp.classic_address)

# Ping the ledger
try:
    ping = client.request({"command": "server_info"})
    print("OK: Ledger reachable")
except Exception as e:
    print("ERROR: Ledger unreachable:", e)
"@

Write-Host "🔍 Running Python validation..."
$out = $py | python
Write-Host $out

if ($out -match "ERROR") {
    Write-Error "❌ Validation failed. Fix before continuing."
}

Write-Host "✅ Step 1 Complete — Validation Passed" -ForegroundColor Green
