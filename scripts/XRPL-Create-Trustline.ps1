param(
    [Parameter(Mandatory=$true)]
    [string]$Seed,

    [Parameter(Mandatory=$true)]
    [string]$Issuer,

    [string]$Currency = "COPX",
    [string]$Limit = "10000000000",
    [string]$RpcUrl = "https://s.altnet.rippletest.net:51234"
)

Write-Host "🚀 Creating trustline (xrpl-py 3.0.0)..." -ForegroundColor Cyan

# Build temporary Python script
$tmp = New-TemporaryFile

$py = @"
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import TrustSet
from xrpl.transaction import autofill, sign, submit_and_wait

seed = "$Seed"
issuer = "$Issuer"
currency = "$Currency"
limit = "$Limit"
rpc = "$RpcUrl"

wallet = Wallet.from_seed(seed)
client = JsonRpcClient(rpc)

tx = TrustSet(
    account = wallet.classic_address,
    limit_amount = {
        "currency": currency,
        "issuer": issuer,
        "value": limit
    }
)

tx_filled = autofill(tx, client)
signed = sign(tx_filled, wallet)
result = submit_and_wait(signed, client)

print(result)
"@

Set-Content -Path $tmp -Value $py -Encoding utf8

python $tmp

Remove-Item $tmp
