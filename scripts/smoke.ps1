param(
  [string]$Pair = "XRP/COL",
  [int]$Steps = 60,
  [int]$Seed = 42
)

$ErrorActionPreference = "Stop"

# Resolve repo root robustly (works via run_ci.ps1 or direct)
$here = if ($PSScriptRoot) { $PSScriptRoot }
elseif ($PSCommandPath) { Split-Path -Parent $PSCommandPath }
elseif (Test-Path (Join-Path (Get-Location) "scripts")) { (Resolve-Path (Join-Path (Get-Location) "scripts")).Path }
else { (Get-Location).Path }

$repo = (Resolve-Path (Join-Path $here '..')).Path
$py   = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# Ensure artifacts dir
$art = Join-Path $repo ".artifacts"
New-Item -ItemType Directory -Force -Path $art | Out-Null

# Ensure dev deps
$req = Join-Path $repo "requirements-dev.txt"
if (Test-Path $req) {
  & $py -m pip install -q -r $req | Out-Null
}

# 1) Tests (importlib avoids path aliasing issues)
Push-Location $repo
try {
  & $py -m pytest -q . --import-mode=importlib *>&1 |
    Tee-Object -FilePath (Join-Path $art "pytest.txt")
}
finally { Pop-Location }

# 2) Run MVP sim (real if present, else fallback in run_sim.ps1)
& (Join-Path $repo "scripts\run_sim.ps1") -Pair $Pair -Steps $Steps -Seed $Seed

# 3) Ensure index.html links for sim outputs (idempotent)
$idx = Join-Path $art "index.html"
if (Test-Path $idx) {
  $cur = Get-Content $idx -Raw
  if ($cur -notmatch 'sim\.events\.ndjson') {
    $extra = @"
  <li><a href="sim.events.ndjson">sim.events.ndjson</a></li>
  <li><a href="sim.metrics.json">sim.metrics.json</a></li>
  <li><a href="sim.summary.csv">sim.summary.csv</a></li>
"@
    $cur = $cur -replace '(?s)(</ul>)', "$extra`n`$1"
    Set-Content $idx -Encoding utf8 -Value $cur
  }
}

Write-Host "Smoke complete ✔  Artifacts in .\.artifacts"
