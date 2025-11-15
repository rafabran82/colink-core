if (-not (Get-Command Show-CiNotification -ErrorAction SilentlyContinue)) {
  function Show-CiNotification {
    param(
      [string]$Title,
      [string]$Message,
      [bool]$IsError = $false
    )
    $tag = if ($IsError) { "[CI-ERROR]" } else { "[CI-INFO]" }
    Write-Host "$tag $Title - $Message"
  }
}
if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
  function Write-Log {
    param(
      [string]$Prefix,
      [string]$Context,
      [string]$Message,
      [bool]$IsError = $false
    )

    $tag = "[{0}][{1}]" -f $Prefix, $Context
    if ($IsError) {
      Write-Host "$tag $Message" -ForegroundColor Red
    } else {
      Write-Host "$tag $Message" -ForegroundColor Cyan
    }
  }
}
if (-not (Test-Path variable:ciScript)) {
  $ciScript = Join-Path $PSScriptRoot 'Local-CI.ps1'
}
Write-Host ""
Write-Host "======================================"
Write-Host "🟢 EWS-MASTER: ALL CHECKS PASSED" -ForegroundColor Green
Write-Host "======================================"
Write-Host ""

# --- 4) Run Local CI, only after EWS success ---
Write-Host "▶ STEP 2: Local CI pipeline (scripts\Local-CI.ps1)..." -ForegroundColor Yellow

& $ciScript
$ciExit = $LASTEXITCODE

Write-Host ""

if ($ciExit -eq 0) {
  Write-Host "🟢 Guard-All: Local CI succeeded (exit code $ciExit)." -ForegroundColor Green
  Write-Log -Prefix "EWS" -Context "Guarded CI" -Message "Local CI succeeded (exit code $ciExit)." -IsError $false
  Show-CiNotification -Title "COLINK Guarded CI" -Message "Success: EWS + Local CI completed successfully." -IsError $false
} else {
  Write-Host "🔴 Guard-All: Local CI failed with exit code $ciExit." -ForegroundColor Red
  Write-Log -Prefix "EWS" -Context "Guarded CI" -Message "Local CI failed (exit code $ciExit)." -IsError $true
}



