Write-Host "Running test bootstrap script..."

# Reference to /scripts directory (parent of this script)
$root = Split-Path $PSScriptRoot -Parent       # scripts\
$me   = Join-Path $PSScriptRoot "ci.test-bootstrap.ps1"

# Required files using correct path resolution
$requiredFiles = @(
    (Join-Path $root "ci.smoke.ps1"),
    (Join-Path $root "Run-LP-Full.ps1"),
    $me
)

Write-Host "`nChecking required files..."
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "âœ” File exists: $file"
    } else {
        Write-Host "âŒ File missing: $file"
    }
}

# Backend (Node.js) check
$backend = Get-Process | Where-Object {$_.Name -like "*node*"}
if ($backend) {
    Write-Host "âœ” Backend service (Node.js) is running."
} else {
    Write-Host "âŒ Backend service NOT running."
}

# Check environment variables
Write-Host "`nChecking environment variables..."
$envVars = @("XRPL_TEST_ACCOUNT", "NODE_ENV")

foreach ($envVar in $envVars) {
    $value = Get-Item "env:$envVar" -ErrorAction SilentlyContinue
    if ($value) {
        Write-Host "âœ” Environment variable $envVar is set."
    } else {
        Write-Host "âŒ Environment variable $envVar is NOT set."
    }
}

# Simulate final test logic
Start-Sleep -Seconds 1
Write-Host "`nTest bootstrap script executed successfully!"

