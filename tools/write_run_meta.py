#!/usr/bin/env python3
import json, os, pathlib, platform, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART  = ROOT / ".artifacts"
ART.mkdir(parents=True, exist_ok=True)

doc = {
    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    "os": os.environ.get("OS_NAME") or platform.platform(),
    "sha": os.environ.get("GIT_SHA"),
    "backend": os.environ.get("BACKEND"),
    "python": platform.python_version(),
    "schema_version": 1
}
(ART / "run_meta.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("Wrote ./.artifacts/run_meta.json")
