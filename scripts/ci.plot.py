# scripts/ci.plot.py  — clean, stable plotter (no weird indentation)

import argparse, os, re, sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")

def looks_iso(s: str) -> bool:
    return bool(ISO_RE.match(str(s or "")))

def thin_xticks(ax, m_hint: int | None = None) -> None:
    """
    Always produce a small set of categorical ticks that fits.
    If the x-data are strings, we place ticks at 4 evenly spread indices.
    """
    try:
        labels = [lb.get_text() for lb in ax.get_xticklabels() if lb.get_text() != ""]
        m = len(labels) if labels else (m_hint or 0)
        if m <= 0:
            return
        # pick first, ~33%, ~66%, last (unique & sorted)
        raw = [0, 1/3, 2/3, 1]
        idx = sorted(set(int(round(p*(m-1))) for p in raw)) if m > 1 else [0]
        ax.xaxis.set_major_locator(FixedLocator(idx))
        # rotate & avoid clipping
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        ax.figure.subplots_adjust(bottom=0.25)
    except Exception:
        # never fail plotting because of tick formatting
        pass

def read_runs(csv_path: str) -> pd.DataFrame | None:
    if not os.path.exists(csv_path):
        print(f"[WARN] Log file not found: {csv_path}")
        return None
    # Try headerless, then with header
    try:
        df = pd.read_csv(csv_path, names=["Timestamp", "Files", "SizeMB"], dtype=str)
    except Exception:
        df = pd.read_csv(csv_path, dtype=str)

    # If a header is present, normalize column names
    cols = {c.lower(): c for c in df.columns}
    tcol = cols.get("timestamp", "Timestamp")
    fcol = cols.get("files", "Files")
    scol = cols.get("sizemb", "SizeMB")

    df = df[[tcol, fcol, scol]].rename(columns={tcol:"Timestamp", fcol:"Files", scol:"SizeMB"})

    df = df[df["Timestamp"].apply(looks_iso)]
    df["Files"]  = pd.to_numeric(df["Files"], errors="coerce")
    df["SizeMB"] = pd.to_numeric(df["SizeMB"], errors="coerce")
    df = df.dropna(subset=["Files","SizeMB"])
    # keep last 50 points
    if len(df) > 50:
        df = df.tail(50)
    return df

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=r".artifacts/ci/runs/runs_log.csv")
    ap.add_argument("--out", default=r".artifacts/ci/runs/runs_trend.png")
    args = ap.parse_args()

    df = read_runs(args.csv)
    if df is None or df.empty:
        # nothing to plot; not an error
        return 0

    fig, ax1 = plt.subplots(figsize=(6, 3))
    ax1.plot(df["Timestamp"], df["SizeMB"], marker="o", label="Total MB")
    ax1.set_xlabel("Run Timestamp")
    ax1.set_ylabel("Total MB")
    ax1.ticklabel_format(style="plain", axis="y")
    ax1.get_yaxis().get_major_formatter().set_scientific(False)
    ax1.yaxis.get_offset_text().set_visible(False)

    ax2 = ax1.twinx()
    ax2.plot(df["Timestamp"], df["Files"], marker="x", label="Files")
    ax2.set_ylabel("Files")

    fig.suptitle("Local CI Run Trend")

    # Ensure x-axis labels are thinned & readable
    thin_xticks(ax1, m_hint=len(df))

    fig.tight_layout()
    plt.savefig(args.out, dpi=150)
    print("[OK] Trend chart written:", args.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
