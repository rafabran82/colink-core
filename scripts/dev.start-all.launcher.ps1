# COLINK "Start Everything" dev launcher
# Option A: Start API + Frontend + Dashboard (no CI)

$repoRoot = "C:\Users\sk8br\Desktop\colink-core"
Set-Location $repoRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 COLINK Start Everything (API + Frontend)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1) Start API backend in its own PowerShell window
Write-Host "▶ Starting API backend in a new window..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    '-NoLogo',
    '-NoExit',
    '-File',
    "$repoRoot\scripts\dev.api.launcher.ps1"
)

# 2) Start frontend dashboard in its own PowerShell window
Write-Host "▶ Starting frontend dashboard in a new window..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    '-NoLogo',
    '-NoExit',
    '-File',
    "$repoRoot\scripts\dev.frontend.launcher.ps1"
)

# 3) Open dashboard index.html if it exists
$indexPath = Join-Path $repoRoot ".artifacts\index.html"

Write-Host ""
if (Test-Path $indexPath) {
    Write-Host "▶ Opening existing dashboard index.html..." -ForegroundColor Yellow
    Start-Process $indexPath
} else {
    Write-Host "ℹ️ No .artifacts\\index.html yet." -ForegroundColor DarkYellow
    Write-Host "   Run COLINK Guarded CI once to generate the dashboard." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "✅ COLINK Start Everything launched API + Frontend." -ForegroundColor Green
Write-Host "   (Each is running in its own PowerShell window.)" -ForegroundColor Green
