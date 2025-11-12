import csv, json, os, sys, pathlib, datetime

REPO = pathlib.Path(__file__).resolve().parents[1]
ART   = REPO / ".artifacts"
DATA  = ART / "data"
METR  = ART / "metrics"
METR.mkdir(parents=True, exist_ok=True)

CSV_PATH    = METR / "summary.csv"
JSON_PATH   = METR / "summary.json"
NDJSON_PATH = METR / "summary.ndjson"

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_metrics_from_runs():
    rows = []
    if not DATA.exists():
        return rows
    for run_dir in sorted(DATA.iterdir()):
        if not run_dir.is_dir():
            continue
        m = run_dir / "metrics.json"
        if not m.exists():
            continue
        try:
            obj = json.loads(m.read_text(encoding="utf-8"))
        except Exception:
            continue
        rec = {"run_id": run_dir.name, "timestamp_utc": utc_now()}
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        rec[f"{k}_{k2}"] = v2
                else:
                    rec[k] = v
        rows.append(rec)
    return rows

def read_existing_csv_header():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        try:
            return next(r)
        except StopIteration:
            return []

def write_csv(rows):
    header = set(read_existing_csv_header())
    for r in rows:
        header.update(r.keys())
    header = ["run_id","timestamp_utc"] + sorted([h for h in header if h not in ("run_id","timestamp_utc")])

    existing = []
    if CSV_PATH.exists():
        with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
            dr = csv.DictReader(f)
            for row in dr:
                existing.append(row)

    by_id = { row.get("run_id"): row for row in existing if "run_id" in row }
    for r in rows:
        by_id[r.get("run_id")] = r

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for row in sorted(by_id.values(), key=lambda x: x.get("run_id","")):
            w.writerow({k: row.get(k, "") for k in header})

def write_json(rows):
    by_id = {}
    if JSON_PATH.exists():
        try:
            arr = json.loads(JSON_PATH.read_text(encoding="utf-8"))
            for r in arr:
                if isinstance(r, dict) and "run_id" in r:
                    by_id[r["run_id"]] = r
        except Exception:
            pass
    for r in rows:
        by_id[r["run_id"]] = r
    JSON_PATH.write_text(json.dumps(list(sorted(by_id.values(), key=lambda x: x.get("run_id",""))), indent=2), encoding="utf-8")

def write_ndjson(rows):
    seen = set()
    if NDJSON_PATH.exists():
        for line in NDJSON_PATH.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
                rid = obj.get("run_id")
                if rid: seen.add(rid)
            except Exception:
                pass
    with NDJSON_PATH.open("a", encoding="utf-8") as f:
        for r in rows:
            if r.get("run_id") in seen:
                continue
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    rows = load_metrics_from_runs()
    if not rows:
        print("⚠️ No metrics found.", file=sys.stderr)
        return 0
    write_csv(rows)
    write_json(rows)
    write_ndjson(rows)
    print(f"✅ Metrics summary written: {CSV_PATH} / {JSON_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

