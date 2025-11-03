# ===== COLINK Phase II Manager (XRPL Testnet) =====
# Location-aware, safe-by-default, DRY_RUN-ready

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path (Split-Path -Parent $ScriptDir)  # repo root

$EnvFile = ".\.env.testnet"

function Show-Menu {
  Write-Host ""
  Write-Host "COLINK Phase II – XRPL Manager" -ForegroundColor Cyan
  Write-Host "1) Activate venv / Install deps"
  Write-Host "2) Validate .env.testnet"
  Write-Host "3) Issue COPX (mock) + Trustline (DRY by default)"
  Write-Host "4) Seed Liquidity (COL/COPX, COL/XRP) offers (DRY by default)"
  Write-Host "5) Run Swap Tests / Quotes"
  Write-Host "6) Run Compliance Monitor Stub"
  Write-Host "7) Git add/commit/push"
  Write-Host "0) Exit"
}

function Activate-Venv {
  if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    python -m venv .venv
  }
  . .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install "xrpl-py>=2.3,<3" python-dotenv==1.0.1
  Write-Host "Venv ready." -ForegroundColor Green
}

function Validate-Env {
  if (-not (Test-Path $EnvFile)) { Write-Error "Missing $EnvFile"; return $false }
  $envs = Get-Content $EnvFile | Where-Object {$_ -and ($_ -notmatch '^\s*#')}
  $must = @(
    "XRPL_ENDPOINT","XRPL_ISSUER_SEED","XRPL_ISSUER_ADDRESS",
    "XRPL_HOT_SEED","XRPL_HOT_ADDRESS","COPX_CODE","DRY_RUN"
  )
  $ok = $true
  foreach ($k in $must) {
    if (-not ($envs -match ("^$k="))) { Write-Warning "Missing key: $k"; $ok=$false }
  }
  if ($ok) { Write-Host "Env looks good." -ForegroundColor Green }
  return $ok
}

function Py-Run($path) {
  if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found in PATH/venv."; return
  }
  if (-not (Test-Path $path)) { Write-Error "Missing script: $path"; return }
  python $path
}

function Issue-COPX { Py-Run ".\phase2\xrpl\copx_issuer.py" }
function Seed-Liquidity { Py-Run ".\phase2\xrpl\seed_liquidity.py" }
function Swap-Tests { Py-Run ".\phase2\xrpl\swap_tests.py" }
function Compliance-Monitor { Py-Run ".\phase2\xrpl\compliance_monitor_stub.py" }

function Git-Commit-Push {
  git add .
  $msg = "Phase II: initial XRPL testnet scaffolding (issuer, liquidity, swaps, compliance stub)"
  git commit -m $msg
  git push -u origin HEAD
  Write-Host "Committed & pushed." -ForegroundColor Green
}

do {
  Show-Menu
  $choice = Read-Host "Select"
  switch ($choice) {
    "1" { Activate-Venv }
    "2" { Validate-Env | Out-Null }
    "3" { if (Validate-Env) { Issue-COPX } }
    "4" { if (Validate-Env) { Seed-Liquidity } }
    "5" { if (Validate-Env) { Swap-Tests } }
    "6" { if (Validate-Env) { Compliance-Monitor } }
    "7" { Git-Commit-Push }
    "0" { break }
    default { Write-Host "Unknown option." }
  }
} while ($true)
