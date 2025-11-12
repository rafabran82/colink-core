#!/usr/bin/env python3
"""
Phase 4: XRPL Testnet bootstrap (DRY-RUN SCAFFOLD)
- No network calls yet; just args + plan output.
- Next commit wires xrpl-py behind --execute.
"""
import argparse, os, json, time, pathlib

def load_env():
    env = {}
    p = pathlib.Path(".env")
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: 
                continue
            k,v = line.split("=",1)
            env[k.strip()] = v.strip()
    return env

def main():
    ap = argparse.ArgumentParser(description="XRPL Testnet bootstrap (dry-run)")
    ap.add_argument("--network", default=os.getenv("XRPL_NETWORK","testnet"), choices=["testnet","devnet"])
    ap.add_argument("--out", default=".artifacts/data/bootstrap", help="Output folder")
    ap.add_argument("--token-code", default=os.getenv("XRPL_TOKEN_CODE","COL"))
    ap.add_argument("--execute", action="store_true", help="(future) perform real xrpl ops")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    env = load_env()
    run = {
        "ts": int(time.time()),
        "network": args.network,
        "token_code": args.token_code,
        "execute": args.execute,
        "env_keys": sorted([k for k in env.keys() if k.startswith("XRPL_")]),
        "plan": [
            "Create/derive issuer, LP, and user wallets (seed if provided; else generate)",
            "Fund wallets via faucet (testnet/devnet)",
            "Set trustlines (user↔issuer, LP↔issuer) for token",
            "Issue token from issuer",
            "Seed basic DEX offers for COL/XRP"
        ]
    }

    plan_path = out / f"bootstrap_plan_{args.network}.json"
    plan_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(f"OK: wrote bootstrap plan → {plan_path}")
    print("NOTE: --execute is ignored in this scaffold. Next step wires xrpl-py calls.")

if __name__ == "__main__":
    main()
