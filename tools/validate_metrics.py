#!/usr/bin/env python3
import json
import pathlib
import sys

from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts"
SCHEMA_PATH = ROOT / "tools" / "metrics.schema.json"


def load_schema():
    # tolerate BOM
    with open(SCHEMA_PATH, encoding="utf-8-sig") as f:
        return json.load(f)


def candidate_jsons() -> list[pathlib.Path]:
    if not ARTIFACTS.exists():
        return []
    return list(ARTIFACTS.rglob("*.json"))


def main():
    schema = load_schema()
    validator = Draft202012Validator(schema)

    files = candidate_jsons()
    if not files:
        print("No JSON files found under .artifacts/. Did the sim runner emit anything?")
        sys.exit(2)

    metrics_files = []
    failed = 0
    for p in files:
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print(f"[SKIP] {p}: invalid JSON: {e}")
            continue

        if isinstance(data, dict) and isinstance(data.get("metrics"), dict):
            metrics_files.append(p)
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

    if not metrics_files:
        print(
            "Found JSONs but none looked like metrics (missing top-level 'metrics' object).",
            file=sys.stderr,
        )
        sys.exit(4)

    if failed:
        print(f"Validation failed: {failed} file(s) invalid.")
        sys.exit(1)

    print(f"Validated {len(metrics_files)} metrics JSON file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

