# ============================================
# GUARD-PYTHONPATH
# Ensures project root is added to PYTHONPATH
# ============================================

param()

Write-Host "🔍 Checking PYTHONPATH..." -ForegroundColor Cyan

# Project root = parent folder of /scripts
$projectRoot = Split-Path $PSScriptRoot -Parent

if (-not $env:PYTHONPATH) {
    Write-Host "ℹ️ PYTHONPATH not set, initializing..." -ForegroundColor Yellow
    $env:PYTHONPATH = $projectRoot
} elseif ($env:PYTHONPATH -notmatch [regex]::Escape($projectRoot)) {
    Write-Host "➕ Appending project root to PYTHONPATH..." -ForegroundColor Yellow
    $env:PYTHONPATH = "$($env:PYTHONPATH);$projectRoot"
} else {
    Write-Host "✅ Project root already present in PYTHONPATH"
}

# Final health summary
Write-Host ""
Write-Host "===================================="
Write-Host "🟢 PYTHONPATH GUARD: OK"
Write-Host "   PYTHONPATH = $env:PYTHONPATH"
Write-Host "===================================="
