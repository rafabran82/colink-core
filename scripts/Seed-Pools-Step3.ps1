# ================================
# Seed-Pools-Step3.ps1
# DEX Offer Plan (Dry Run Only)
# ================================
param(
    [string]$Network = "testnet"
)

$ErrorActionPreference = "Stop"

Write-Host "📐 COLINK Pool Seeding — Step 3 (DEX Offer Plan)" -ForegroundColor Cyan

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
# Python: fetch balances + propose DEX offers
# ------------------------------------------------------------
$py = @"
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountLines, AccountInfo
import json, sys

issuer_seed = "$issuer_seed"
user_seed = "$user_seed"
lp_seed   = "$lp_seed"

issuer = Wallet.from_seed(issuer_seed)
user   = Wallet.from_seed(user_seed)
lp     = Wallet.from_seed(lp_seed)

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

def xrp_balance(addr):
    info = client.request(AccountInfo(account=addr, ledger_index="validated"))
    return float(info.result.get("account_data", {}).get("Balance", 0)) / 1_000_000

def ic_balances(addr):
    out = {}
    lines = client.request(AccountLines(account=addr, ledger_index="validated")).result.get("lines", [])
    for l in lines:
        key = f"{l['currency']}:{l['account']}"
        out[key] = {
            "balance": float(l["balance"]),
            "limit": float(l["limit"])
        }
    return out

# ---- Fetch balances ----
u_xrp = xrp_balance(user.classic_address)
l_xrp = xrp_balance(lp.classic_address)

u_ic = ic_balances(user.classic_address)
l_ic = ic_balances(lp.classic_address)

print("=== USER BALANCES ===")
print(json.dumps({"xrp": u_xrp, "ic": u_ic}, indent=2))

print("=== LP BALANCES ===")
print(json.dumps({"xrp": l_xrp, "ic": l_ic}, indent=2))

# ---- Build DEX Plan ----
plan = {
    "COL/XRP": {
        "user_offers": {
            "sell_COL": 500000,
            "buy_XRP": 50
        },
        "lp_offers": {
            "sell_COL": 500000,
            "buy_XRP": 50
        }
    },
    "CPX/XRP": {
        "user_offers": {
            "sell_CPX": 500000,
            "buy_XRP": 50
        },
        "lp_offers": {
            "sell_CPX": 500000,
            "buy_XRP": 50
        }
    }
}

print("=== DEX OFFER PLAN (DRY RUN) ===")
print(json.dumps(plan, indent=2))
"@

Write-Host "🔍 Running Python to build DEX plan..."
$out = $py | python

Write-Host $out

if ($out -match "Traceback") {
    Write-Error "❌ Python error detected."
}

Write-Host "✅ Step 3 Complete — DEX Offer Plan Generated" -ForegroundColor Green
