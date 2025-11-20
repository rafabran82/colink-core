# =======================================
# ðŸ›¡ COLINK Pre-Commit Hook Installer
# =======================================
$ErrorActionPreference = "Stop"

Write-Host "======================================"
Write-Host "ðŸ›¡ Installing/Updating COLINK Pre-Commit Hook"
Write-Host "======================================"

# Resolve Git root
$gitRoot = git rev-parse --show-toplevel 2>$null
if (-not $gitRoot) {
    Write-Host "âŒ ERROR: Not inside a Git repository." -ForegroundColor Red
    exit 1
}

# Hooks folder & pre-commit path
$hooksDir = Join-Path $gitRoot ".git\hooks"
$preCommit = Join-Path $hooksDir "pre-commit"

# Ensure hooks folder exists
if (-not (Test-Path $hooksDir)) {
    Write-Host "ðŸ”§ Creating hooks directory..."
    New-Item -ItemType Directory -Path $hooksDir | Out-Null
}

# ----------------------------
# Pre-commit hook content
# ----------------------------
$hookContent = @'
#!/usr/bin/env pwsh
# COLINK Pre-Commit Safety Hook

Write-Host "ðŸ›¡ COLINK Safety Hook Activated"

$guard = "$(git rev-parse --show-toplevel)/scripts/EWS-DELETION-GUARD.ps1"

if (Test-Path $guard) {
    pwsh -NoProfile -ExecutionPolicy Bypass -File $guard
    if ($LASTEXITCODE -ne 0) {
        Write-Host "â›” Commit blocked by deletion guard." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "âš ï¸  Deletion guard script missing â€” skipping" -ForegroundColor Yellow
}

Write-Host "ðŸŸ¢ All pre-commit safety checks passed."
exit 0
'@

# Write the hook to file
Set-Content -Path $preCommit -Value $hookContent -Encoding UTF8

# Make the hook executable
cmd.exe /c "icacls `"$preCommit`" /grant:r *S-1-1-0:(RX)" > $null 2>&1

Write-Host "======================================"
Write-Host "ðŸŸ¢ Pre-commit hook installed/updated at $preCommit"
Write-Host "======================================"

