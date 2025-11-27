# EWS-Install-Hooks.ps1
$ErrorActionPreference = "Stop"

Write-Host "======================================"
Write-Host "🛡  Installing COLINK Git Safety Hooks"
Write-Host "======================================"

$gitDir = Join-Path $PSScriptRoot "..\.git"
$hooksDir = Join-Path $gitDir "hooks"
$preCommit = Join-Path $hooksDir "pre-commit"

if (-not (Test-Path $gitDir)) {
    Write-Host "❌ ERROR: .git directory not found. Run this from inside the repo." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $hooksDir)) {
    Write-Host "🔧 Creating hooks directory..."
    New-Item -ItemType Directory -Path $hooksDir | Out-Null
}

Write-Host "🔧 Writing pre-commit hook..."

$hook = @'
#!/usr/bin/env pwsh
# COLINK Pre-Commit Safety Hook

Write-Host "🛡  COLINK Safety Hook Activated"

# Run deletion guard
$guard = "$(git rev-parse --show-toplevel)/scripts/EWS-DELETION-GUARD.ps1"

if (Test-Path $guard) {
    pwsh -NoProfile -ExecutionPolicy Bypass -File $guard
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⛔ Commit blocked by deletion guard." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Deletion guard script missing — skipping" -ForegroundColor Yellow
}

Write-Host "🟢 All pre-commit safety checks passed."
exit 0

