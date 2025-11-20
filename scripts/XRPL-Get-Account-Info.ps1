param(
    [Parameter(Mandatory=$true)]
    [string] $Address,

    [string] $RpcUrl = "https://s.altnet.rippletest.net:51234"
)

Write-Host "🔍 Fetching account info for $Address ..." -ForegroundColor Cyan

# 1) Create temp Python file
$tmp = New-TemporaryFile

# 2) Python code
$py = @"
import json, sys
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo

address = sys.argv[1]
rpc = sys.argv[2]

client = JsonRpcClient(rpc)

req = AccountInfo(
    account=address,
    ledger_index="validated",
    strict=True
)

try:
    response = client.request(req)
    print(json.dumps(response.result, indent=2))
except Exception as e:
    print("ERROR:", e)
"@

# 3) Write python file
Set-Content -Path $tmp -Encoding utf8 -Value $py

# 4) Execute
python $tmp $Address $RpcUrl

# 5) Cleanup
Remove-Item $tmp -ErrorAction SilentlyContinue
