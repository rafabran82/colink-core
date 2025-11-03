import os, json
from pathlib import Path
print(json.dumps({
  "cwd": str(Path.cwd()),
  "env": {
    "XRPL_TAKER_ADDRESS": os.getenv("XRPL_TAKER_ADDRESS"),
    "XRPL_TAKER_SEED": "***" if os.getenv("XRPL_TAKER_SEED") else None,
    "XRPL_MAKER_ADDRESS": os.getenv("XRPL_MAKER_ADDRESS"),
    "XRPL_ISSUER_ADDRESS": os.getenv("XRPL_ISSUER_ADDRESS"),
    "XRPL_ISSUER_SEED": "***" if os.getenv("XRPL_ISSUER_SEED") else None,
    "OTC_XRP_DROPS": os.getenv("OTC_XRP_DROPS"),
    "OTC_COPX_QTY": os.getenv("OTC_COPX_QTY"),
    "COPX_CODE": os.getenv("COPX_CODE"),
    "XRPL_RPC": os.getenv("XRPL_RPC"),
  }
}, indent=2))
