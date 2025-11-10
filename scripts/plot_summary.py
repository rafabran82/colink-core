import csv, sys, os
import matplotlib.pyplot as plt

art = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".artifacts"))
csv_path = os.path.join(art, "sim.summary.csv")
png_path = os.path.join(art, "summary.png")

if not os.path.exists(csv_path):
    print("No sim.summary.csv; skipping plot.")
    sys.exit(0)

xs, ys = [], []
with open(csv_path, newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        # Use generic columns; fall back if missing
        step = int(row.get("step") or row.get("Step") or len(xs))
        metric = float(row.get("metric", row.get("Metric", row.get("price", row.get("Price", 0)))) or 0)
        xs.append(step)
        ys.append(metric)

plt.figure()
plt.plot(xs, ys)
plt.title("Simulation summary")
plt.xlabel("step")
plt.ylabel("metric")
plt.tight_layout()
plt.savefig(png_path, dpi=120)
print("Wrote", png_path)
