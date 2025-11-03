$ErrorActionPreference="Stop"
$code = @"
import os
from xrpl.wallet import Wallet
keys=["XRPL_TAKER_SEED","XRPL_MAKER_SEED","XRPL_HOT_SEED","XRPL_ISSUER_SEED","BIDDER_SEED","TAKER_SEED"]
for k in keys:
    s=os.environ.get(k)
    if not s: continue
    try:
        print(f"{k} => {Wallet.from_seed(s).classic_address}")
    except Exception as e:
        print(f"{k} => [bad seed] {e}")
"@
$tmp = Join-Path $env:TEMP ("seedmap_{0}.py" -f ([guid]::NewGuid()))
Set-Content $tmp $code -Encoding UTF8
python $tmp
