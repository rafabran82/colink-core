#!/usr/bin/env python3
import json, sys, pathlib
from typing import List
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts"
SCHEMA_PATH = ROOT / "tools" / "metrics.schema.json"

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def find_metric_files() -> List[pathlib.Path]:
    if not ARTIFACTS.exists():
        return []
    return list(ARTIFACTS.rglob("*.metrics.json"))

def main():
    schema = load_schema()
    validator = Draft202012Validator(schema)

    files = find_metric_files()
    if not files:
        print("No metrics files found under .artifacts/. Did the sim runner emit JSON?")
        sys.exit(2)

    failed = 0
    for p in files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[FAIL] {p}: invalid JSON: {e}")
            failed += 1
            continue

        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            print(f"[FAIL] {p}: schema violations:")
            for e in errors:
                loc = "/".join(str(x) for x in e.path) or "(root)"
                print(f"  - at {loc}: {e.message}")
            failed += 1
        else:
            rid = data.get("run_id", "(no run_id)")
            print(f"[OK]   {p} (run_id={rid})")

    if failed:
        print(f"Validation failed: {failed} file(s) invalid.")
        sys.exit(1)

    print(f"All {len(files)} metrics files are valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())


