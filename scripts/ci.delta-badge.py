import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_DIR = os.path.join(REPO, ".artifacts", "metrics")
SUMMARY_JSON = os.path.join(METRICS_DIR, "summary.json")
DELTA_JSON   = os.path.join(METRICS_DIR, "delta.json")

def load_summary():
    if not os.path.exists(SUMMARY_JSON):
        return []
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict) and "rows" in data:
                data = data["rows"]
            return data if isinstance(data, list) else []
        except Exception:
            return []

# label, key, unit, decimals, higher_is_better
CANDIDATES = [
    ("Success Rate", "success_rate", "%", 2, True),
    ("p95 Latency", "latency_ms_p95", " ms", 0, False),
    ("p50 Latency", "latency_ms_p50", " ms", 0, False),
    ("Max Latency", "latency_ms_max", " ms", 0, False),
    ("Files",       "files", "", 0, True),
    ("Total MB",    "total_mb", " MB", 1, True),
]

def fmt(value, decimals):
    if value is None:
        return None
    try:
        return round(float(value), decimals)
    except Exception:
        return None

def main():
    rows = load_summary()
    if len(rows) < 1:
        # nothing to do
        with open(DELTA_JSON, "w", encoding="utf-8") as f:
            json.dump({"items":[]}, f, ensure_ascii=False, indent=2)
        print("⚠️ No metrics found for delta.")
        return 0
    if len(rows) == 1:
        # only current available
        cur = rows[-1]
        out = {
            "current_timestamp": cur.get("ts") or cur.get("timestamp"),
            "previous_timestamp": None,
            "items":[]
        }
        with open(DELTA_JSON, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("ℹ️ Only one run available — delta skipped.")
        return 0

    prev, cur = rows[-2], rows[-1]
    items = []
    for label, key, unit, decimals, higher_is_better in CANDIDATES:
        c = cur.get(key)
        p = prev.get(key)
        if c is None or p is None:
            continue
        try:
            c = float(c); p = float(p)
        except Exception:
            continue
        delta = c - p
        improved = (delta > 0) if higher_is_better else (delta < 0)
        items.append({
            "key": key,
            "label": label,
            "current": fmt(c, decimals),
            "previous": fmt(p, decimals),
            "delta": fmt(delta, decimals),
            "unit": unit,
            "higher_is_better": higher_is_better,
            "improved": improved
        })

    out = {
        "current_timestamp": cur.get("ts") or cur.get("timestamp"),
        "previous_timestamp": prev.get("ts") or prev.get("timestamp"),
        "items": items
    }
    os.makedirs(METRICS_DIR, exist_ok=True)
    with open(DELTA_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"✅ Delta summary written: {DELTA_JSON}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
