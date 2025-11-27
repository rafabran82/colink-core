# =========================================
# ci.smoke.ps1 â€” COLINK smoke health check
# =========================================

Write-Host "Checking if Node.js is installed..."
node -v
if ($?) {
    Write-Host "Node.js is installed."
    $nodeStatus = "Installed"
} else {
    Write-Host "Node.js is NOT installed."
    $nodeStatus = "Missing"
}

Write-Host "Checking PowerShell script execution..."
$testScript = ".\ci\ci.test-bootstrap.ps1"
if (Test-Path $testScript) {
    Write-Host "Test script found: $testScript"
    & $testScript
    $scriptStatus = "Executed"
} else {
    Write-Host "Test script NOT found at: $testScript"
    $scriptStatus = "Missing"
}

Write-Host "Checking Python installation..."
python --version
if ($?) {
    Write-Host "Python is installed."
    $pythonStatus = "Installed"
} else {
    Write-Host "Python is NOT installed."
    $pythonStatus = "Missing"
}

Write-Host "Checking if backend (Node.js) service is running..."
$backend = Get-Process | Where-Object {$_.Name -like "*node*"}
if ($backend) {
    Write-Host "Backend service is running."
    $backendStatus = "Running"
} else {
    Write-Host "Backend service is NOT running."
    $backendStatus = "Stopped"
}

# -----------------------------
# Health Summary
# -----------------------------
Write-Host ""
Write-Host "==============================="
Write-Host "ðŸ”¥ Health Summary:"
Write-Host "==============================="
Write-Host "Node.js Status:          $nodeStatus"
Write-Host "Test Script Status:      $scriptStatus"
Write-Host "Python Status:           $pythonStatus"
Write-Host "Backend Service Status:  $backendStatus"

if ($nodeStatus -eq "Installed" -and
    $scriptStatus -eq "Executed" -and
    $pythonStatus -eq "Installed" -and
    $backendStatus -eq "Running") {

    Write-Host "âœ… All checks passed successfully! COLINK system is healthy and ready for the next steps!"
}
else {
    Write-Host "âŒ Some checks failed. Please inspect above output."
}

Write-Host "COLINK Smoke Test completed."

