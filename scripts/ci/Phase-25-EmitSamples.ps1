param()
$ErrorActionPreference = "Stop"

Write-Host "== Phase-25: Emit sample artifacts (fallback) ==" -ForegroundColor Cyan

$art = Join-Path $PWD ".artifacts"
if (-not (Test-Path $art)) { New-Item -ItemType Directory -Force -Path $art | Out-Null }

# Only create samples if the dir is basically empty (probe + manifest aside)
$existing = Get-ChildItem -Path $art -File -Recurse -ErrorAction SilentlyContinue | Where-Object {
  $_.Name -notin @("_probe.txt","ci.manifest.json")
}
if ($existing) {
  Write-Host "Artifacts already exist; skipping sample emission." -ForegroundColor DarkYellow
  return
}

# 1) CSV
"ts,value" | Set-Content (Join-Path $art "demo.csv")
(Get-Date).ToString("s") + ",42" | Add-Content (Join-Path $art "demo.csv")

# 2) NDJSON
'{"ts":"'+(Get-Date).ToString("s")+'","event":"demo-start"}' | Set-Content (Join-Path $art "demo.events.ndjson")
'{"ts":"'+(Get-Date).ToString("s")+'","event":"demo-end"}'   | Add-Content (Join-Path $art "demo.events.ndjson")

# 3) metrics JSON
@{
  schema_version = "1.0"
  created_at     = (Get-Date).ToString("s")
  metrics        = @{ count = 2; mean = 42.0 }
} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $art "run.metrics.json") -Encoding utf8

# 4) Parquet (best-effort via pandas/pyarrow)
$py = Join-Path $PWD ".venv\Scripts\python.exe"
if (Test-Path $py) {
  $code = @"
import pandas as pd, datetime as dt, pyarrow as pa, pyarrow.parquet as pq
from pathlib import Path
art = Path(r'$art')
df = pd.DataFrame([{'ts': pd.Timestamp.utcnow(), 'value': 42}])
table = pa.Table.from_pandas(df)
pq.write_table(table, art/'demo.parquet')
"@
  try { & $py - <<#PY# $code PY
  } catch { Write-Warning "Parquet emit failed (ok to ignore)." }
}

# 5) SUMMARY.md and tiny PNG placeholder
@"
# CI Summary

- Created: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
- Files: demo.csv, demo.events.ndjson, run.metrics.json, demo.parquet (if available)
"@ | Set-Content (Join-Path $art "SUMMARY.md") -Encoding utf8

# Make a 1x1 PNG via PowerShell (BMP->PNG fallback using .NET)
$pngPath = Join-Path $art "summary.png"
try {
  Add-Type -AssemblyName System.Drawing
  $bmp = New-Object System.Drawing.Bitmap 1,1
  $bmp.SetPixel(0,0,[System.Drawing.Color]::FromArgb(0,120,215))
  $bmp.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose()
} catch {
  # Fallback: write a text marker if System.Drawing is unavailable
  "PNG placeholder" | Set-Content (Join-Path $art "summary.png.txt")
}

Write-Host "Sample artifacts emitted." -ForegroundColor Green
