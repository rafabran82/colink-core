#!/usr/bin/env python3
"""
COLINK XRPL Testnet bootstrap skeleton.

This is a temporary, side-effect-free bootstrap script that only prepares
artifact files so that CI and local tooling have something to point at.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path


def _write_json(path_obj: Path, obj) -> None:
    path_obj.write_text(json.dumps(obj, indent=2))


def _append_tx_note(txlog_path: Path, note: str) -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = {"ts": ts, "note": str(note)}
    with txlog_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    p = argparse.ArgumentParser(prog="xrpl.testnet.bootstrap")
    p.add_argument(
        "--network",
        default="testnet",
        choices=["testnet", "devnet", "amm-devnet", "mainnet"],
    )
    p.add_argument("--out", default=".artifacts/data/bootstrap")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=(logging.DEBUG if args.verbose else logging.INFO),
        format="%(message)s",
    )
    logging.info(
        "bootstrap(skeleton): network=%s execute=%s out=%s",
        args.network,
        args.execute,
        args.out,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ensure tx_log.ndjson exists with at least one line
    txlog_path = out_dir / "tx_log.ndjson"
    if not txlog_path.exists():
        _append_tx_note(txlog_path, "bootstrap skeleton started")

    # Ensure base JSON files exist
    base_files = [
        ("wallets.json", {"issuer": None, "user": None, "lp": None}),
        ("trustlines.json", []),
        ("offers.json", []),
    ]
    for name, default in base_files:
        pth = out_dir / name
        if not pth.exists():
            _write_json(pth, default)

    # Plan / Result / Meta / Human summary
    plan_path = out_dir / f"bootstrap_plan_{args.network}.json"
    result_path = out_dir / f"bootstrap_result_{args.network}.json"
    meta_path = out_dir / "bootstrap_meta.json"
    human_path = out_dir / f"bootstrap_summary_{args.network}.txt"

    if not plan_path.exists():
        plan = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "network": args.network,
            "steps": ["ensure-files", "write-plan", "write-result"],
            "execute": bool(args.execute),
        }
        _write_json(plan_path, plan)

    result = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "network": args.network,
        "executed": False,
        "notes": ["skeleton run; no XRPL side-effects yet"],
    }
    if result_path.exists():
        try:
            prev = json.loads(result_path.read_text())
            if isinstance(prev, dict):
                prev.update(result)
                result = prev
        except Exception:
            pass
    _write_json(result_path, result)

    meta = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "skeleton main completed",
        "exit_code": 0,
    }
    if meta_path.exists():
        try:
            prev = json.loads(meta_path.read_text())
            if isinstance(prev, dict):
                prev.update(meta)
                meta = prev
        except Exception:
            pass
    _write_json(meta_path, meta)

    # Human readable summary
    names = [
        "wallets.json",
        "trustlines.json",
        "offers.json",
        "tx_log.ndjson",
        "bootstrap_meta.json",
        f"bootstrap_plan_{args.network}.json",
        f"bootstrap_result_{args.network}.json",
        f"bootstrap_summary_{args.network}.txt",
    ]
    present = [n for n in names if (out_dir / n).exists()]

    try:
        if txlog_path.exists():
            with txlog_path.open("r", encoding="utf-8") as fh:
                tx_lines = sum(1 for line in fh if line.strip())
        else:
            tx_lines = 0
    except Exception:
        tx_lines = 0

    human_lines = [
        "COLINK XRPL Testnet Bootstrap — summary",
        f"UTC: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"Folder: {args.out}",
        "Present: " + ", ".join(present),
        f"tx_log lines: {tx_lines}",
        "OK: True",
    ]
    human_path.write_text("\n".join(human_lines), encoding="utf-8")

    logging.info("bootstrap(skeleton): wrote artifacts into %s", str(out_dir))
    _append_tx_note(txlog_path, "skeleton finished")

    return 0


if __name__ == "__main__":
    sys.exit(main())
