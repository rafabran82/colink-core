#!/usr/bin/env python3
import argparse, os, json, datetime

def main():
    parser = argparse.ArgumentParser(description="COLINK simulation runner (safe default mode)")
    parser.add_argument("--out", default=".artifacts/data/demo", help="output directory for metrics")
    parser.add_argument("--n", type=int, default=10, help="number of samples to generate")
    parser.add_argument("--dt", type=float, default=0.1, help="time step between samples")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.out, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(args.out, f"metrics_{timestamp}.json")

    # Generate mock metrics
    data = {
        "timestamp": timestamp,
        "runs": args.n,
        "dt": args.dt,
        "values": [round(i * args.dt, 4) for i in range(args.n)]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Metrics written to {path}")
    return 0

if __name__ == "__main__":
    main()
