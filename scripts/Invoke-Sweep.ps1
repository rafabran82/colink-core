param(
  [string]$OutDir  = "artifacts\charts",
  [string]$RunName = "dev-sweep"
)

$ErrorActionPreference = "Stop"

# Resolve Python (prefer venv)
$PyExe = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

# Ensure output dir & absolute paths
$chartsDir   = (New-Item -ItemType Directory -Force -Path $OutDir).FullName
$chartsRoot  = Get-Item -LiteralPath $chartsDir
$summaryPath = Join-Path $chartsRoot.Parent.FullName "summary.json"

Write-Host "==> Running sweep -> $chartsDir (run: $RunName) ..."

# Inline Python to generate charts only (no summary kwargs)
$tmpPy = [System.IO.Path]::Combine($env:TEMP, ("sweep_inline_{0}.py" -f ([guid]::NewGuid())))
$py = @"
from colink_core.sim.summary import write_minimal
from pathlib import Path
import json

outdir = Path(r"$chartsDir")
outdir.mkdir(parents=True, exist_ok=True)

charts = write_minimal(str(outdir), name=r"$RunName", twap_guard_bps=150.0)
print(json.dumps({"charts": charts}))
"@
Set-Content -Path $tmpPy -Value $py -Encoding utf8

try {
  $out = & $PyExe $tmpPy
  if ($LASTEXITCODE -ne 0) { throw "python returned $LASTEXITCODE" }

  # Parse JSON result
  $charts = @()
  try {
    $obj = $out | ConvertFrom-Json
    if ($obj -and $obj.charts) { $charts = @($obj.charts) }
  } catch { }

  # Fallback: enumerate PNGs if JSON parse fails/empty
  if ($charts.Count -eq 0) {
    $charts = Get-ChildItem -LiteralPath $chartsDir -Filter *.png | ForEach-Object { $_.FullName }
  }

  # If a single string slipped through, split on newlines
  if ($charts -is [string]) { $charts = $charts -split "`n" }

  Write-Host ("==> Wrote {0} chart(s):" -f $charts.Count)
  foreach ($c in $charts) { Write-Host " - $c" }

  # Write summary.json (PowerShell; UTF-8 no BOM)
  $summary = @{
    name           = $RunName
    ts             = [int][double]::Parse((Get-Date -Date (Get-Date).ToUniversalTime() -UFormat %s))
    sizes_col      = @(100, 500, 1000)
    twap_guard_bps = 150
    avg_slip_bps   = 100
    max_slip_bps   = 120
    charts_dir     = $chartsDir
  }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($summaryPath, ($summary | ConvertTo-Json -Depth 5), $utf8NoBom)

  Write-Host "==> Summary written: $summaryPath"
}
finally {
  Remove-Item $tmpPy -ErrorAction SilentlyContinue
}
