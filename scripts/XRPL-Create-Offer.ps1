param(
    [Parameter(Mandatory=$true)]
    [string] $Seed,

    [Parameter(Mandatory=$true)]
    [string] $TakerPaysCurrency,

    [Parameter(Mandatory=$true)]
    [string] $TakerPaysValue,

    [Parameter(Mandatory=$true)]
    [string] $TakerGetsCurrency,

    [Parameter(Mandatory=$true)]
    [string] $TakerGetsIssuer,

    [Parameter(Mandatory=$true)]
    [string] $TakerGetsValue,

    [string] $RpcUrl = "https://s.altnet.rippletest.net:51234"
)

Write-Host "💱 Creating DEX Offer on XRPL..." -ForegroundColor Cyan

# 1) Create temp python file
$tmp = New-TemporaryFile

# 2) Python code
$py = @"
import json, sys
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import autofill, sign, submit_and_wait

seed = sys.argv[1]
tp_currency = sys.argv[2]
tp_value = sys.argv[3]
tg_currency = sys.argv[4]
tg_issuer = sys.argv[5]
tg_value = sys.argv[6]
rpc = sys.argv[7]

client = JsonRpcClient(rpc)
wallet = Wallet.from_seed(seed)

# ---- taker_pays ----
if tp_currency.upper() == "XRP":
    taker_pays = tp_value
else:
    taker_pays = IssuedCurrencyAmount(
        currency=tp_currency,
        issuer=wallet.classic_address,
        value=tp_value
    )

# ---- taker_gets ----
taker_gets = IssuedCurrencyAmount(
    currency=tg_currency,
    issuer=tg_issuer,
    value=tg_value
)

tx = OfferCreate(
    account=wallet.classic_address,
    taker_pays=taker_pays,
    taker_gets=taker_gets
)

try:
    filled = autofill(tx, client)
    signed = sign(filled, wallet)
    result = submit_and_wait(signed, client)
    print(json.dumps(result.result, indent=2))
except Exception as e:
    print("ERROR:", e)
"@

# 3) Write temp file
Set-Content -Path $tmp -Encoding UTF8 -Value $py

# 4) Execute python
python $tmp `
    $Seed `
    $TakerPaysCurrency `
    $TakerPaysValue `
    $TakerGetsCurrency `
    $TakerGetsIssuer `
    $TakerGetsValue `
    $RpcUrl

# 5) Cleanup
Remove-Item $tmp -ErrorAction SilentlyContinue

Write-Host "🟢 Offer submitted." -ForegroundColor Green
