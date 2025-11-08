import os, pathlib, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
csv  = ROOT / ".artifacts" / "dataset.csv"
out  = os.environ.get("GITHUB_STEP_SUMMARY")

if csv.exists() and out:
    df = pd.read_csv(csv)
    md = []
    md.append("## COLINK Phase 3 — Simulation Summary")
    md.append("")
    md.append(f"Rows: **{len(df)}**")
    md.append("")
    md.append(df.head(10).to_markdown(index=False))
    with open(out, "a", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Wrote summary to {out}")
else:
    print("No dataset.csv or GITHUB_STEP_SUMMARY not set.")
