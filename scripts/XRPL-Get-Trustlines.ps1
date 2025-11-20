param(
    [Parameter(Mandatory=$true)]
    [string] $Address,

    [string] $RpcUrl = "https://s.altnet.rippletest.net:51234"
)

Write-Host "🔍 Fetching trustlines for $Address ..." -ForegroundColor Cyan

# 1) Temp Python file
$tmp = New-TemporaryFile

# 2) Python (uses AccountLines request, xrpl-py 3.0.0 compatible)
$py = @"
import json, sys, asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests import AccountLines

address = sys.argv[1]
rpc = sys.argv[2]

async def main():
    client = AsyncJsonRpcClient(rpc)
    req = AccountLines(account=address)
    resp = await client.request(req)
    print(json.dumps(resp.result, indent=2))

try:
    asyncio.run(main())
except Exception as e:
    print("ERROR:", e)
"@

# 3) Write Python
Set-Content -Path $tmp -Encoding utf8 -Value $py

# 4) Execute Python
python $tmp $Address $RpcUrl

# 5) Cleanup
Remove-Item $tmp -ErrorAction SilentlyContinue
