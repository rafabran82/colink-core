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

    # Parse timestamps and build compact HH:MM labels
    df["Time"]  = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Time"])
    df["Label"] = df["Time"].dt.strftime("%H:%M")

    # Keep last 50 for readability
    if len(df) > 50:
        df = df.tail(50)

    # Plot using numeric x positions + HH:MM tick labels (prevents overlap)
    x = list(range(len(df)))

    fig, ax1 = plt.subplots(figsize=(6,3))
    ax1.plot(x, df["SizeMB"], marker="o", color="tab:blue", label="Total MB")
    ax1.set_xlabel("Run Timestamp")
    ax1.set_ylabel("Total MB", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(x, df["Files"], marker="x", color="tab:orange", label="Files")
    ax2.set_ylabel("Files", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    # X-axis labels (HH:MM), rotate & thin if many points
    ax1.set_xticks(x)
    labels = df["Label"].tolist()
    if len(labels) > 16:
        step = max(1, len(labels)//12)
        for i in range(len(labels)):
            if i % step != 0:
                labels[i] = ""  # thin labels for readability
    ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)

    fig.suptitle("Local CI Run Trend")
    fig.tight_layout()
    plt.savefig(OUT, dpi=150)
    print("[OK] Trend chart written:", OUT)

if __name__ == "__main__":
    main()
