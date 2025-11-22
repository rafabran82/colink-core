param(
    [Parameter(Mandatory=$true)]
    [string] $Seed,

    [Parameter(Mandatory=$true)]
    [string] $Destination,

    [Parameter(Mandatory=$true)]
    [string] $CurrencyHex,

    [Parameter(Mandatory=$true)]
    [string] $Amount,

    [string] $RpcUrl = "https://s.altnet.rippletest.net:51234"
)

Write-Host "💸 Issuing COPX to $Destination ..." -ForegroundColor Cyan

$tmp = New-TemporaryFile

$py = @"
import sys, json
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill, sign, submit_and_wait

seed = sys.argv[1]
destination = sys.argv[2]
currency = sys.argv[3]
amount = sys.argv[4]
rpc = sys.argv[5]

client = JsonRpcClient(rpc)
wallet = Wallet.from_seed(seed)

issued = IssuedCurrencyAmount(
    currency=currency,
    issuer=wallet.classic_address,
    value=amount
)

tx = Payment(
    account=wallet.classic_address,
    destination=destination,
    amount=issued
)

try:
    filled = autofill(tx, client)
    signed = sign(filled, wallet)
    result = submit_and_wait(signed, client)
    print(json.dumps(result.result, indent=2))
except Exception as e:
    print("ERROR:", e)
"@

Set-Content -Path $tmp -Encoding utf8 -Value $py
python $tmp $Seed $Destination $CurrencyHex $Amount $RpcUrl
Remove-Item $tmp -ErrorAction SilentlyContinue

Write-Host "🟢 COPX issued." -ForegroundColor Green
