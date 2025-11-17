# == Phase-25: Emit sample artifacts (fallback, venv-aware) ==
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $true

$artifacts = Join-Path (Get-Location) ".artifacts"
New-Item -ItemType Directory -Force -Path $artifacts | Out-Null

# Prefer venv Python
if ($env:VIRTUAL_ENV -and (Test-Path (Join-Path $env:VIRTUAL_ENV "Scripts/python.exe"))) {
  $python = Join-Path $env:VIRTUAL_ENV "Scripts/python.exe"
} else {
  $python = "python"
}
Write-Host "== Phase-25: Emit sample artifacts (fallback) =="
Write-Host "Using python: $python"
Write-Host "Artifacts dir: $artifacts"

# --- Write and run a tiny Python helper using stdlib; parquet is best-effort ---
$py = @"
import os, json, csv, time
art = os.path.join(os.getcwd(), ".artifacts")
os.makedirs(art, exist_ok=True)
rows = [{"t": i, "value": i*i} for i in range(5)]

with open(os.path.join(art, "dataset.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

with open(os.path.join(art, "sample.metrics.json"), "w") as f:
    json.dump({"schema_version":"1.0", "ts": time.time()}, f, indent=2)

with open(os.path.join(art, "sample.events.ndjson"), "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\\n")

print("Wrote CSV/JSON/NDJSON")

# Parquet is optional; skip silently if deps missing
try:
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(art, "dataset.parquet"))
    print("Wrote dataset.parquet via pandas/pyarrow")
except Exception as e:
    print("Parquet skipped:", e)
"@

$tmpPy = [IO.Path]::Combine([IO.Path]::GetTempPath(), "emit_{0}.py" -f ([guid]::NewGuid()))
Set-Content -Path $tmpPy -Value $py -Encoding utf8

& $python $tmpPy
$code = $LASTEXITCODE
Write-Host "EmitSamples Python exit code: $code (ignored)"
exit 0
