# == Phase-25: Emit sample artifacts (fallback, venv-aware) ==
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $true

# Resolve artifacts dir in the current workspace
$artifacts = Join-Path (Get-Location) ".artifacts"
New-Item -ItemType Directory -Force -Path $artifacts | Out-Null

# Prefer the venv's python, fallback to PATH
if ($env:VIRTUAL_ENV -and (Test-Path (Join-Path $env:VIRTUAL_ENV "Scripts/python.exe"))) {
  $python = Join-Path $env:VIRTUAL_ENV "Scripts/python.exe"
} else {
  $python = "python"
}

Write-Host "== Phase-25: Emit sample artifacts (fallback) =="
Write-Host "Using python: $python"
Write-Host "Artifacts dir: $artifacts"

# Inline Python: write CSV/NDJSON/JSON via stdlib; Parquet via pandas/pyarrow if available
$py = @"
import os, json, csv, time, sys
art = os.path.join(os.getcwd(), ".artifacts")
os.makedirs(art, exist_ok=True)

rows = [{"t": i, "value": i*i} for i in range(5)]

with open(os.path.join(art, "dataset.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

with open(os.path.join(art, "sample.metrics.json"), "w") as f:
    json.dump({"schema_version":"1.0", "os": os.name, "ts": time.time()}, f, indent=2)

with open(os.path.join(art, "sample.events.ndjson"), "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\\n")

print("Wrote CSV/JSON/NDJSON")

# Optional Parquet: try pandas/pyarrow if present; otherwise skip gracefully
try:
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(art, "dataset.parquet"))
    print("Wrote dataset.parquet via pandas/pyarrow")
except Exception as e:
    print("Parquet skipped:", e)
"@

# Write temp file and run
$tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "emit_parquet_{0}.py" -f ([guid]::NewGuid()))
Set-Content -Path $tmp -Value $py -Encoding utf8

& $python $tmp
$code = $LASTEXITCODE
Write-Host "EmitSamples Python exit code: $code (ignored)"

# Always succeed: Phase-25 is optional
exit 0
