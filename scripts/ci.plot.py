import pandas as pd, matplotlib.pyplot as plt, os, re

RUNS = r".artifacts/ci/runs/runs_log.csv"
OUT  = r".artifacts/ci/runs/runs_trend.png"

def looks_like_iso_ts(s: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", s or ""))

def main():
    if not os.path.exists(RUNS):
        print("[WARN] Log file not found:", RUNS)
        return
    df = pd.read_csv(RUNS, names=["Timestamp","Files","SizeMB"], dtype=str)

    # Clean rows and coerce numbers
    df = df[df["Timestamp"].astype(str).apply(looks_like_iso_ts)]
    df["Files"]  = pd.to_numeric(df["Files"],  errors="coerce")
    df["SizeMB"] = pd.to_numeric(df["SizeMB"], errors="coerce")
    df = df.dropna(subset=["Files","SizeMB"])

    # Last 50 for readability
    if len(df) > 50:
        df = df.tail(50)

    fig, ax1 = plt.subplots(figsize=(6,3))
    ax1.plot(df["Timestamp"], df["SizeMB"], marker="o", color="tab:blue", label="Total MB")
    ax1.set_xlabel("Run Timestamp")
    ax1.set_ylabel("Total MB", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(df["Timestamp"], df["Files"], marker="x", color="tab:orange", label="Files")
    ax2.set_ylabel("Files", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    fig.suptitle("Local CI Run Trend")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    fig.tight_layout()
    plt.savefig(OUT, dpi=150)
    print("[OK] Trend chart written:", OUT)

if __name__ == "__main__":
    main()
