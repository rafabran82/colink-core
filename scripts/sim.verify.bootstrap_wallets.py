import json
from pathlib import Path

def main():
    root = Path(".artifacts/data/bootstrap")
    wallets_path = root / "wallets.json"

    print("=== Phase 3 Wallet Injection Verification ===")

    # 1) Check file exists
    if not wallets_path.exists():
        print("ERROR: wallets.json not found at:", wallets_path)
        return 1

    # 2) Check JSON loads
    try:
        wallets = json.loads(wallets_path.read_text())
    except Exception as e:
        print("ERROR: wallets.json failed to parse:", e)
        return 1

    # 3) Validate required fields
    required = ["issuer", "user", "lp"]
    for key in required:
        if key not in wallets:
            print(f"ERROR: Missing {key} wallet entry")
            return 1
        if not isinstance(wallets[key], dict):
            print(f"ERROR: {key} is not a dict: {wallets[key]}")
            return 1

        for field in ["address", "seed", "public", "private"]:
            if field not in wallets[key]:
                print(f"ERROR: {key} wallet missing field {field}")
                return 1

    print("PHASE 3 WALLET INJECTION: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
