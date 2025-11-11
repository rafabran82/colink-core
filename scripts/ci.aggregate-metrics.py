import json, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
import datetime as dt

root = Path(".artifacts/data")
rows = []
for run_dir in sorted(root.glob("*")):
    metrics_file = run_dir / "metrics.json"
    if not metrics_file.exists(): continue
    with open(metrics_file) as f:
        m = json.load(f)
    m["run_id"] = run_dir.name
    m["timestamp"] = dt.datetime.strptime(run_dir.name, "%Y%m%d-%H%M%S")
    rows.append(m)

if not rows:
    print("⚠️ No metrics found.")
    exit(0)

df = pd.DataFrame(rows).sort_values("timestamp")
metrics_dir = Path(".artifacts/metrics")
metrics_dir.mkdir(parents=True, exist_ok=True)
csv_path = metrics_dir / "summary.csv"
json_path = metrics_dir / "summary.json"
plot_path = metrics_dir / "summary.png"

df.to_csv(csv_path, index=False)
df.to_json(json_path, orient="records", indent=2)

plt.figure(figsize=(8,4))
if "success_rate" in df:
    plt.plot(df["timestamp"], df["success_rate"], marker="o", label="Success %")
if "avg_latency_ms" in df:
    plt.plot(df["timestamp"], df["avg_latency_ms"], marker="o", label="Latency (ms)")
plt.title("COLINK Simulation Metrics Trend")
plt.xlabel("Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(plot_path)
print(f"✅ Metrics summary written: {csv_path} / {json_path} / {plot_path}")
