#!/usr/bin/env python3
import argparse
import os
import json
import datetime
import sys

CONFIG_PATH = "simulation.config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["meta"]["timestamp"] = datetime.datetime.utcnow().isoformat()
    return config

def main():
    parser = argparse.ArgumentParser(
        description="COLINK Phase 3 Simulation Runner (config loader stage)"
    )
    parser.add_argument("--out", default=".artifacts/data", help="Output folder")
    args = parser.parse_args()

    config = load_config()

    os.makedirs(args.out, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(args.out, f"sim_config_load_{timestamp}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"OK: Loaded config and wrote a debug copy to:")
    print(f" -> {out_file}")
    return 0

if __name__ == "__main__":
    main()
