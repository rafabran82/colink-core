# ===============================================
# 🧪 COLINK Developer Environment Smoke Test
# ===============================================

Write-Host "==============================================="
Write-Host "🧪 COLINK Developer Environment Smoke Test"
Write-Host "==============================================="

$errors = @()

# ------------------------------------------------
# 1) Node.js Check
# ------------------------------------------------
Write-Host "`n🔍 Checking Node.js installation..."
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✔ Node.js: $nodeVersion"
    } else {
        Write-Host "❌ Node.js not installed!"
        $errors += "Node.js missing"
    }
} catch {
    Write-Host "❌ Node.js not installed!"
    $errors += "Node.js missing"
}

# ------------------------------------------------
# 2) Python Check
# ------------------------------------------------
Write-Host "`n🔍 Checking Python installation..."
try {
    $pyVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✔ Python: $pyVersion"
    } else {
        Write-Host "❌ Python not installed!"
        $errors += "Python missing"
    }
} catch {
    Write-Host "❌ Python not installed!"
    $errors += "Python missing"
}

# ------------------------------------------------
# 3) XRPL Environment Variables
# ------------------------------------------------
Write-Host "`n🔍 Checking required XRPL environment variables..."

$requiredEnv = @(
    "XRPL_TEST_ACCOUNT",
    "NODE_ENV"
)

foreach ($envVar in $requiredEnv) {
    $value = Get-Item -Path "Env:$envVar" -ErrorAction SilentlyContinue
    if ($value) {
        Write-Host "✔ $envVar is set"
    } else {
        Write-Host "❌ $envVar is NOT set"
        $errors += "$envVar missing"
    }
}

# ------------------------------------------------
# 4) Check Backend (Node API) running on port 5000
# ------------------------------------------------
Write-Host "`n🔍 Checking backend service (port 5000)..."

$backend = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($backend) {
    Write-Host "✔ Backend service is RUNNING (port 5000)"
} else {
    Write-Host "❌ Backend service is NOT running"
    $errors += "Backend API not running"
}

# ------------------------------------------------
# 5) Check Dashboard (React) on port 3000 (optional)
# ------------------------------------------------
Write-Host "`n🔍 Checking dashboard (port 3000)..."

$dash = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($dash) {
    Write-Host "✔ Dashboard is RUNNING (port 3000)"
} else {
    Write-Host "⚠️ Dashboard not running (optional)"
}

# ------------------------------------------------
# 6) Required COLINK Scripts Exist
# ------------------------------------------------
Write-Host "`n🔍 Checking required COLINK scripts..."

$requiredScripts = @(
    "Run-LP-Full.ps1",
    "ci.smoke.ps1",
    "XRPL-Rollup.ps1",
    "XRPL-Collect.ps1",
    "sim.run.py"
)

foreach ($script in $requiredScripts) {
    $path = Join-Path $PSScriptRoot $script
    if (Test-Path $path) {
        Write-Host "✔ $script found"
    } else {
        Write-Host "❌ $script NOT found"
        $errors += "$script missing"
    }
}

# ------------------------------------------------
# 7) Artifact Directory Health Check
# ------------------------------------------------
Write-Host "`n🔍 Checking artifact directory structure..."

$requiredDirs = @(
    "..\.artifacts",
    "..\.artifacts\ci",
    "..\.artifacts\data",
    "..\.artifacts\bundles",
    "..\.artifacts\metrics",
    "..\.artifacts\plots",
    "..\.artifacts\runs"
)

foreach ($dir in $requiredDirs) {
    $full = Join-Path $PSScriptRoot $dir
    if (Test-Path $full) {
        Write-Host "✔ $dir"
    } else {
        Write-Host "❌ Missing: $dir"
        $errors += "$dir missing"
    }
}

# ------------------------------------------------
# 8) HEALTH SUMMARY
# ------------------------------------------------
Write-Host "`n==============================================="
Write-Host "📊 HEALTH SUMMARY"
Write-Host "==============================================="

if ($errors.Count -eq 0) {
    Write-Host "🟢 All checks passed — Dev environment is HEALTHY and READY!" -ForegroundColor Green
} else {
    Write-Host "🟥 Issues detected:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "   • $err"
    }
    Write-Host "`n⚠️ Please fix the issues above."
}

Write-Host "`n🧪 dev-smoke.ps1 completed."
