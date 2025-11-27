import os
import pathlib

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / ".artifacts"
csv = ART / "dataset.csv"
out = os.environ.get("GITHUB_STEP_SUMMARY")

if csv.exists():
    df = pd.read_csv(csv)
    # Chart: events_count by run_id (simple bar)
    if not df.empty and "run_id" in df.columns and "events_count" in df.columns:
        fig, ax = plt.subplots()
        g = df.groupby("run_id", dropna=False)["events_count"].sum()
        g.plot(kind="bar", ax=ax)
        ax.set_title("Events per run")
        ax.set_xlabel("run_id")
        ax.set_ylabel("events_count")
        img_path = ART / "summary.png"
        fig.tight_layout()
        fig.savefig(img_path, dpi=150)
        plt.close(fig)

    if out:
        lines = []
        lines.append("## COLINK Phase 3 - Simulation Summary")
        lines.append("")
        lines.append(f"Rows: **{len(df)}**")
        lines.append("")
        # Table head
        head_cols = [
            c
            for c in df.columns
            if c
            in [
                "run_id",
                "timestamp",
                "backend",
                "os",
                "sha",
                "events_count",
                "success_rate",
                "p95_latency_ms",
            ]
        ]
        if head_cols:
            lines.append(df[head_cols].head(10).to_markdown(index=False))
            lines.append("")
        # Embed chart if created
        if (ART / "summary.png").exists():
            lines.append("![events per run](.artifacts/summary.png)")
            lines.append("")
        with open(out, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Wrote summary to {out}")
    else:
        print("GITHUB_STEP_SUMMARY not set; summary only saved as files.")
else:
    print("No dataset.csv; nothing to summarize.")

