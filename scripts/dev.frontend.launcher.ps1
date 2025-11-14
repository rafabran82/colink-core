# COLINK dashboard/frontend dev launcher (auto-detects npm script)

$dashboardDir = "C:\Users\sk8br\Desktop\colink-core\colink-dashboard"
Set-Location $dashboardDir

Write-Host "Starting COLINK dashboard (frontend)..." -ForegroundColor Cyan
Write-Host ""

$pkgPath = Join-Path $dashboardDir "package.json"

if (-not (Test-Path $pkgPath)) {
    Write-Host "❌ package.json not found in $dashboardDir" -ForegroundColor Red
    exit 1
}

try {
    $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
} catch {
    Write-Host "❌ Failed to parse package.json" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

$scriptName = $null

if ($pkg.scripts.dev) {
    $scriptName = "dev"
} elseif ($pkg.scripts.start) {
    $scriptName = "start"
} elseif ($pkg.scripts.serve) {
    $scriptName = "serve"
}

if (-not $scriptName) {
    Write-Host "❌ Could not find a suitable frontend script (dev/start/serve) in package.json" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available scripts are:" -ForegroundColor Yellow
    npm run
    exit 1
}

Write-Host "▶ Using npm script: $scriptName" -ForegroundColor Yellow
Write-Host ""

npm run $scriptName
