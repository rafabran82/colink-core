param(
  [string]$Issuer     = "rBvZJP5WNGipMyScwFGFmDRAvcaFyn3LBY",
  [int]   $DropsPer   = 250,      # drops per 1 COPX
  [int]   $AskA       = 1000,     # COPX size A
  [int]   $AskB       = 250,      # COPX size B
  [switch]$ShowBooks,
  [switch]$NoCancel
)

$ErrorActionPreference = "Stop"

# Ensure RPC
if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }

# Resolve seeds from env
$seedMaker = $env:XRPL_MAKER_SEED
$seedTaker = $env:XRPL_TAKER_SEED
if (-not $seedMaker -or -not $seedTaker) {
  throw "XRPL_MAKER_SEED or XRPL_TAKER_SEED not set. Load your .env (e.g., .\tools\import_dotenv.ps1 -Path .env.testnet)"
}

# Tools / scripts we rely on
$cancelPS = Join-Path $PSScriptRoot "cancel_offers.ps1"
$bookPS   = Join-Path $PSScriptRoot "book_snapshot.ps1"
$mkInvPy  = Join-Path $PSScriptRoot "..\phase2\xrpl\make_inverse_offer.py"

foreach ($p in @($cancelPS,$mkInvPy)) {
  if (-not (Test-Path $p)) { throw "Missing dependency: $p" }
}

Write-Host "== COPX baseline reset on XRPL testnet ==" -ForegroundColor Cyan
Write-Host "Issuer: $Issuer | Drops/COPX: $DropsPer | Asks: $AskA, $AskB" -ForegroundColor DarkCyan

# 1) Cancel existing COPX offers (both actors)
if (-not $NoCancel) {
  Write-Host "`n-- Cancel (maker) --" -ForegroundColor Yellow
  & $cancelPS -OnlyCOPX -SeedEnv XRPL_MAKER_SEED -NoWait | Write-Output

  Write-Host "`n-- Cancel (taker) --" -ForegroundColor Yellow
  & $cancelPS -OnlyCOPX -SeedEnv XRPL_TAKER_SEED -NoWait | Write-Output

  Start-Sleep -Seconds 2
}

# 2) Post two reference COPX->XRP asks from the *taker* wallet (the one that already holds COPX)
#    make_inverse_offer.py reads TAKER_SEED from env. We'll temporarily set it for the child process.
$prev = $env:TAKER_SEED
$env:TAKER_SEED = $seedTaker
try {
  $dropsA = $AskA * $DropsPer
  $dropsB = $AskB * $DropsPer

  Write-Host "`n-- Post ask A: $AskA COPX for $dropsA drops --" -ForegroundColor Green
  python $mkInvPy --issuer $Issuer --value $AskA --drops $dropsA

  Write-Host "`n-- Post ask B: $AskB COPX for $dropsB drops --" -ForegroundColor Green
  python $mkInvPy --issuer $Issuer --value $AskB --drops $dropsB
}
finally {
  $env:TAKER_SEED = $prev
}

# 3) Optional: show books
if ($ShowBooks -and (Test-Path $bookPS)) {
  Write-Host "`n== Book snapshot ==" -ForegroundColor Cyan
  & $bookPS
} else {
  Write-Host "`nHint: run .\tools\book_snapshot.ps1 to view books." -ForegroundColor DarkGray
}

Write-Host "`n✅ Baseline liquidity reset complete." -ForegroundColor Green
