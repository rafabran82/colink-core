param(
  [switch]$OpenIndex,
  [switch]$SkipParquet = $true,
  [string]$ProjectHook
)

$ErrorActionPreference = "Stop"

function Ensure-Folder([string]$Path) {
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-Python {
  $venvPy = Join-Path .\.venv 'Scripts\python.exe'
  if (Test-Path $venvPy) {
    return (Resolve-Path $venvPy).Path
  }
  $pyCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pyCmd) { return $pyCmd.Source }
  $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
  if ($pyLauncher) {
    $exe = & $pyLauncher.Source -3 -c "import sys; print(sys.executable)"
    if ($LASTEXITCODE -eq 0 -and $exe) { return $exe.Trim() }
  }
  return 'python'
}

function Phase-10 {
  Write-Host "== Phase-10: Bootstrap =="
  $python = Get-Python

  if (-not (Test-Path .\.venv)) {
    & $python -m venv .venv
  }
  $venvPy = Join-Path .\.venv 'Scripts\python.exe'
  if (-not (Test-Path $venvPy)) { throw "Missing venv python at $venvPy" }

  & $venvPy -m pip install --upgrade pip
  try {
    & $venvPy -m pip install pandas pyarrow jsonschema tabulate matplotlib 2>$null
  } catch { Write-Warning "Optional packages failed to install; continuing." }

  Write-Host "Bootstrap complete. Venv:" (Resolve-Path .\.venv)
}

function Phase-20 {
  Write-Host "== Phase-20: Build & Test =="
  $py = Get-Python

  if ($ProjectHook) {
    Write-Host "Running project hook: $ProjectHook"
    Invoke-Expression $ProjectHook
  } else {
    $tmp = Join-Path $env:TEMP ("smoke_{0}.py" -f ([guid]::NewGuid()))
    $smoke = @"
print('Hello from Phase-20. Python OK.')
"@
    Set-Content -Encoding utf8 -Path $tmp -Value $smoke
    & $py $tmp
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  }
  Write-Host "Phase-20 completed."
}

function Emit-Artifacts {
  Write-Host "== Emit-Artifacts =="
  $py = Get-Python
  Ensure-Folder ".artifacts"

  $core = @"
import os, json, csv, time
art = os.path.join(os.getcwd(), ".artifacts")
os.makedirs(art, exist_ok=True)
rows = [{"t": i, "value": i*i} for i in range(10)]

with open(os.path.join(art, "dataset.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

with open(os.path.join(art, "sample.metrics.json"), "w") as f:
    json.dump({"schema_version":"1.0","ts": time.time()}, f, indent=2)

with open(os.path.join(art, "sample.events.ndjson"), "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

print("Wrote CSV/JSON/NDJSON")
"@
  $tmp = Join-Path $env:TEMP ("emit_core_{0}.py" -f ([guid]::NewGuid()))
  Set-Content -Encoding utf8 -Path $tmp -Value $core
  & $py $tmp
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue

  if ($SkipParquet) {
    Write-Host "Parquet skipped by flag (-SkipParquet)."
  } else {
    & $py -c "import importlib, sys; sys.exit(0 if (hasattr(importlib,'util') and importlib.util.find_spec('pandas') and importlib.util.find_spec('pyarrow')) else 1)"
    $canParq = ($LASTEXITCODE -eq 0)
    if ($canParq) {
      $parq = @"
import os, pandas as pd
art = os.path.join(os.getcwd(), ".artifacts")
rows = [{"t": i, "value": i*i} for i in range(10)]
pd.DataFrame(rows).to_parquet(os.path.join(art, "dataset.parquet"))
print("Wrote dataset.parquet")
"@
      $fp = Join-Path $env:TEMP ("emit_parquet_{0}.py" -f ([guid]::NewGuid()))
      Set-Content -Encoding utf8 -Path $fp -Value $parq

      if (Test-Path (Get-Python)) {
        $absPy = (Resolve-Path (Get-Python)).Path
      } else {
        $absPy = (Get-Python)
      }

      $job = Start-Job -ScriptBlock { param($p,$f) & $p $f 2>&1 } -ArgumentList $absPy, $fp
      if (Wait-Job $job -Timeout 8) {
        $out = Receive-Job $job -ErrorAction SilentlyContinue
        if ($out) { $out | Write-Host }
      } else {
        Write-Warning "Parquet generation timed out (skipping)."
        Stop-Job $job -Force | Out-Null
      }
      Remove-Job $job -Force -ErrorAction SilentlyContinue
      Remove-Item $fp -Force -ErrorAction SilentlyContinue
    } else {
      Write-Host "Parquet skipped: pandas/pyarrow not available"
    }
  }

  Write-Host ("Artifacts written:`n - {0}`n - {1}`n - {2}" -f `
    (Resolve-Path .\.artifacts\dataset.csv).Path, `
    (Resolve-Path .\.artifacts\sample.metrics.json).Path, `
    (Resolve-Path .\.artifacts\sample.events.ndjson).Path)
}

function Make-Index {
  Ensure-Folder ".artifacts"
  @"
<!doctype html><meta charset="utf-8"><title>Artifacts</title>
<h1>Artifacts</h1>
<ul>
  <li><a href="dataset.csv">dataset.csv</a></li>
  <li><a href="sample.metrics.json">sample.metrics.json</a></li>
  <li><a href="sample.events.ndjson">sample.events.ndjson</a></li>
  <li><a href="dataset.parquet">dataset.parquet</a> (if present)</li>
</ul>
"@ | Set-Content -Encoding utf8 -Path .\.artifacts\index.html
  Write-Host "index.html written."
}

function Bundle-Artifacts {
  Ensure-Folder ".bundles"
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $zip   = ".bundles\ci-artifacts-$stamp.zip"
  $tgz   = ".bundles\ci-artifacts-$stamp.tgz"

  if (Test-Path $zip) { Remove-Item $zip -Force }
  Compress-Archive -Path .\.artifacts\* -DestinationPath $zip -Force

  $tar = Get-Command tar -ErrorAction SilentlyContinue
  if ($tar) {
    if (Test-Path $tgz) { Remove-Item $tgz -Force }
    Push-Location .\.artifacts
    & $tar -czf "..\$tgz" *
    Pop-Location
    Write-Host "Wrote $tgz"
  } else {
    Write-Host "tar.exe not found; skipped .tgz"
  }
  Write-Host "Wrote $zip"
}

# ===== Orchestrate =====
# >>> AUTO-CD BEGIN <<<
try {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} catch { $scriptDir = (Get-Location).Path }
$repo    = Join-Path $scriptDir 'colink-core'
$didPush = $false
if (Test-Path $repo) {
  Push-Location $repo
  try { $env:PYTHONPATH = (Resolve-Path $repo).Path } catch {}
  $didPush = $true
}
# >>> AUTO-CD END <<<Write-Host "== Local CI: start =="
Phase-10
Phase-20
Emit-Artifacts
Make-Index

Write-Host "Artifacts:"
if (Test-Path .\.artifacts) {
  Get-ChildItem -Recurse .\.artifacts | Format-Table -Auto Name,Length,FullName
}

Bundle-Artifacts
Write-Host "== Local CI: done =="

if ($OpenIndex) {
  $html = Resolve-Path .\.artifacts\index.html
  if (Test-Path $html) { Start-Process $html }
}

# >>> AUTO-CD POP <<<
if ($didPush) { Pop-Location }
# >>> AUTO-CD POP <<<

