import json, csv, pathlib

# Resolve repo root (this script may run from "scripts/")
repo_root = pathlib.Path(__file__).resolve().parents[1]
data_root = repo_root / ".artifacts" / "data"
metrics = []

for f in data_root.glob("*/metrics.json"):
    try:
        data = json.loads(f.read_text())
        data["run_id"] = f.parent.name
        metrics.append(data)
    except Exception as e:
        print(f"⚠️ Failed to parse {f}: {e}")

if not metrics:
    print(f"⚠️ No metrics found in {data_root}")
else:
    out_dir = repo_root / ".artifacts" / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "summary.csv"
    json_path = out_dir / "summary.json"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
        writer.writeheader()
        writer.writerows(metrics)

    json_path.write_text(json.dumps(metrics, indent=2))
    print(f"✅ Metrics summary written: {csv_path} / {json_path}")
