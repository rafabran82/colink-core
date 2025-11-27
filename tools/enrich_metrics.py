#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / ".artifacts"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", default=str(ART))
    ap.add_argument("--os", dest="osname", default=os.environ.get("OS_NAME"))
    ap.add_argument("--sha", default=os.environ.get("GIT_SHA"))
    ap.add_argument("--backend", default=os.environ.get("BACKEND", "Agg"))
    args = ap.parse_args()

    base = pathlib.Path(args.artifacts)
    if not base.exists():
        print(f"No artifacts dir: {base}", file=sys.stderr)
        return 2

    files = sorted(base.rglob("*.metrics.json"))
    if not files:
        print("No metrics JSONs found to enrich.", file=sys.stderr)
        return 3

    changed = 0
    for p in files:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        if "os" not in data or not data["os"]:
            data["os"] = args.osname
        if "sha" not in data or not data["sha"]:
            data["sha"] = args.sha
        if "backend" not in data or not data["backend"]:
            data["backend"] = args.backend
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        changed += 1

    print(f"Enriched {changed} file(s) with os/sha/backend (if missing).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

