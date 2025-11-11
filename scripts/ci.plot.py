import argparse, os, pandas as pd, matplotlib.pyplot as plt

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=r".artifacts/ci/runs/runs_log.csv")
    p.add_argument("--out", default=r".artifacts/ci/runs/runs_trend.png")
    args = p.parse_args()

    runs = args.csv
    out  = args.out

    if not os.path.exists(runs):
        print("[WARN] Log file not found:", runs)
        return

    df = pd.read_csv(runs, names=["Timestamp","Files","SizeMB"], dtype=str)
    import re
    looks = lambda s: bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", str(s or "")))
    df = df[df["Timestamp"].apply(looks)]
    df["Files"]  = pd.to_numeric(df["Files"], errors="coerce")
    df["SizeMB"] = pd.to_numeric(df["SizeMB"], errors="coerce")
    df = df.dropna(subset=["Files","SizeMB"])
    if len(df) > 50: df = df.tail(50)

    fig, ax1 = plt.subplots(figsize=(6,3))
    ax1.plot(df["Timestamp"], df["SizeMB"], marker="o", label="Total MB")
    ax1.set_xlabel("Run Timestamp")
    ax1.set_ylabel("Total MB", color="tab:blue")
    ax1.ticklabel_format(style="plain", axis="y")
    ax1.get_yaxis().get_major_formatter().set_scientific(False)
    ax1.yaxis.get_offset_text().set_visible(False)

    ax2 = ax1.twinx()
    ax2.plot(df["Timestamp"], df["Files"], marker="x", color="tab:orange", label="Files")
    ax2.set_ylabel("Files", color="tab:orange")

    fig.suptitle("Local CI Run Trend")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    fig.tight_layout()
    plt.savefig(out, dpi=150)
    print("[OK] Trend chart written:", out)

if __name__ == "__main__":
    main()

