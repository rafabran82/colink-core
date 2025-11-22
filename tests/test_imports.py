import importlib
import sys

MODULES = [
    "colink_core.config",
    "colink_core.main",
]


def test_imports():
    failed = []
    for m in MODULES:
        try:
            importlib.import_module(m)
        except Exception as e:
            failed.append((m, repr(e)))
    if failed:
        for m, e in failed:
            print(f"[FAIL] {m}: {e}", file=sys.stderr)
        raise AssertionError(f"{len(failed)} import(s) failed")

