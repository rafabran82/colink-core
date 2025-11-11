import json, csv, pathlib

root = pathlib.Path(".artifacts/data")
metrics = []

for f in root.glob("*/metrics.json"):
    try:
        data = json.loads(f.read_text())
        data["run_id"] = f.parent.name
        metrics.append(data)
    except Exception as e:
        print(f"⚠️ Failed to parse {f}: {e}")

if not metrics:
    print("⚠️ No metrics found.")
else:
    out_dir = pathlib.Path(".artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "summary.csv"
    json_path = out_dir / "summary.json"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
        writer.writeheader()
        writer.writerows(metrics)

    json_path.write_text(json.dumps(metrics, indent=2))
    print(f"✅ Metrics summary written: {csv_path} / {json_path}")
