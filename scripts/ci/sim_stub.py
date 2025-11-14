import pathlib, json, csv, datetime as dt
def utc_now_iso(): return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
art = pathlib.Path(".artifacts"); art.mkdir(exist_ok=True)
rows = [(utc_now_iso(), v) for v in (1,2,3)]
with open(art/"demo.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["ts","value"]); w.writerows(rows)
with open(art/"run.metrics.json", "w", encoding="utf-8") as f:
    json.dump({"schema_version":"1.0", "created_at": utc_now_iso(, ensure_ascii=False, indent=2),
               "metrics": {"count": len(rows), "mean": sum(v for _,v in rows)/len(rows)}}, f)
print("sim stub wrote demo.csv + run.metrics.json")
