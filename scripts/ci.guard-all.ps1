#!/usr/bin/env pwsh
<#
  ci.guard-all.ps1

  COLINK Guarded CI launcher:
    1) Runs the Early Warning System master script (EWS-MASTER.ps1).
    2) If and only if EWS passes, runs the Local CI pipeline (Local-CI.ps1).

  This is intended to be your “one button” safety gate before any serious work:
  - EWS catches duplicate routes, bad prefixes, indentation issues, and formatting problems.
  - Local CI runs tests, builds artifacts, and updates the dashboard.

  Exit code:
    - Returns the EWS exit code if EWS fails.
    - Otherwise returns the Local CI exit code.
#>

$ErrorActionPreference = "Stop"

function Show-CiNotification {
    param(
        [string]$Title,
        [string]$Message,
        [bool]$IsError = $false
    )

    try {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        Add-Type -AssemblyName System.Drawing       | Out-Null

        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = if ($IsError) {
            [System.Drawing.SystemIcons]::Error
        } else {
            [System.Drawing.SystemIcons]::Information
        }
        $notify.Visible = $true
        $notify.BalloonTipTitle = $Title
        $notify.BalloonTipText  = $Message
        $notify.BalloonTipIcon  = if ($IsError) {
            [System.Windows.Forms.ToolTipIcon]::Error
        } else {
            [System.Windows.Forms.ToolTipIcon]::Info
        }

        $notify.ShowBalloonTip(5000)
        Start-Sleep -Seconds 6
        $notify.Dispose()
    } catch {
        # Notifications are best-effort; never break CI because of them.
    }
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🛡️  COLINK Guard-All: EWS + Local CI" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# --- 1) Locate Git repo root ---
try {
    $gitRoot = (git rev-parse --show-toplevel).Trim()
} catch {
    Write-Error "❌ Unable to determine Git repository root. Are you inside the colink-core repo?"
    Show-CiNotification -Title "COLINK Guarded CI" -Message "Failed: could not determine Git repo root." -IsError $true
    exit 1
}

if (-not $gitRoot) {
    Write-Error "❌ Git repository root is empty. Aborting."
    Show-CiNotification -Title "COLINK Guarded CI" -Message "Failed: Git repo root was empty." -IsError $true
    exit 1
}

Set-Location $gitRoot

# --- 2) Resolve script paths ---
$ewsScript = Join-Path $gitRoot "scripts\EWS-MASTER.ps1"
$ciScript  = Join-Path $gitRoot "scripts\Local-CI.ps1"

if (-not (Test-Path $ewsScript)) {
    Write-Error "❌ EWS script not found at: $ewsScript"
    Show-CiNotification -Title "COLINK Guarded CI" -Message "Failed: EWS-MASTER.ps1 not found." -IsError $true
    exit 1
}

if (-not (Test-Path $ciScript)) {
    Write-Error "❌ Local CI script not found at: $ciScript"
    Show-CiNotification -Title "COLINK Guarded CI" -Message "Failed: Local-CI.ps1 not found." -IsError $true
    exit 1
}

Write-Host "Repo root: $gitRoot"
Write-Host "EWS script: $ewsScript"
Write-Host "Local CI : $ciScript"
Write-Host ""

# --- 3) Run EWS-MASTER (Early Warning System) ---
Write-Host "▶ STEP 1: Early Warning System (EWS-MASTER)..." -ForegroundColor Yellow

& $ewsScript
$ewsExit = $LASTEXITCODE

if ($ewsExit -ne 0) {
    Write-Host ""
    Write-Host "🔴 Guard-All: EWS-MASTER detected issues (exit code $ewsExit)." -ForegroundColor Red
    Write-Host "    Local CI will NOT run until EWS is clean." -ForegroundColor Red
    Show-CiNotification -Title "COLINK Guarded CI" -Message "EWS failed (exit code $ewsExit). Local CI was skipped." -IsError $true
    exit $ewsExit
}

Write-Host ""
Write-Host "🟢 EWS-MASTER: all checks passed. Proceeding to Local CI..." -ForegroundColor Green
Write-Host ""

# --- 4) Run Local CI, only after EWS success ---
Write-Host "▶ STEP 2: Local CI pipeline (scripts\\Local-CI.ps1)..." -ForegroundColor Yellow

& $ciScript
$ciExit = $LASTEXITCODE

Write-Host ""

if ($ciExit -eq 0) {
    Write-Host "🟢 Guard-All: EWS + Local CI succeeded." -ForegroundColor Green
    Show-CiNotification -Title "COLINK Guarded CI" -Message "Success: EWS + Local CI completed successfully." -IsError $false
} else {
    Write-Host "🔴 Guard-All: Local CI failed with exit code $ciExit." -ForegroundColor Red
    Show-CiNotification -Title "COLINK Guarded CI" -Message "Local CI failed (exit code $ciExit)." -IsError $true
}

exit $ciExit
