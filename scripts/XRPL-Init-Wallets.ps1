Import-Module "$PSScriptRoot\Vault.psm1" -Force

# 1) Load vault
$Vault = Load-Vault

# 2) Function to call Python wallet generator
function New-XRPLWallet {
    $script = Join-Path $PSScriptRoot "xrpl.generate_wallet.py"
    $json = python $script
    return $json | ConvertFrom-Json
}

Write-Host "🔧 Generating new XRPL Testnet wallets..." -ForegroundColor Cyan

# 3) Create Issuer
$issuer = New-XRPLWallet
$Vault.wallets.issuer.seed     = $issuer.seed
$Vault.wallets.issuer.address  = $issuer.address
$Vault.wallets.issuer.created  = (Get-Date).ToString("o")
Write-Host "🏦 Issuer Wallet: $($issuer.address)" -ForegroundColor Yellow

# 4) Create User
$user = New-XRPLWallet
$Vault.wallets.user.seed      = $user.seed
$Vault.wallets.user.address   = $user.address
$Vault.wallets.user.created   = (Get-Date).ToString("o")
Write-Host "👤 User Wallet:   $($user.address)" -ForegroundColor Yellow

# 5) Create LP Wallet
$lp = New-XRPLWallet
$Vault.wallets.lp.seed        = $lp.seed
$Vault.wallets.lp.address     = $lp.address
$Vault.wallets.lp.created     = (Get-Date).ToString("o")
Write-Host "💧 LP Wallet:     $($lp.address)" -ForegroundColor Yellow

# 6) Save updated vault
Save-Vault -Vault $Vault

Write-Host "`n🟢 Wallet initialization complete! Seeds and addresses stored in wallets.vault.json" -ForegroundColor Green
