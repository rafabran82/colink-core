param(
    [switch]$AllowAll
)

Write-Host "🔍 EWS-Deletions-Guard: scanning staged changes..." -ForegroundColor Cyan

# Collect staged deleted files
$deleted = git diff --cached --name-status | Where-Object { $_ -match "^\s*D\s" }

if (-not $deleted -or $AllowAll) {
    Write-Host "🟢 No blocked deletions detected." -ForegroundColor Green
    exit 0
}

Write-Host "🟥 WARNING: The following files are staged for deletion:" -ForegroundColor Red
$deleted | ForEach-Object { Write-Host "   • $_" -ForegroundColor Yellow }

Write-Host ""
Write-Host "❗ This deletion requires confirmation."
$confirm = Read-Host "Type YES to allow this commit, or anything else to cancel"

if ($confirm -eq "YES") {
    Write-Host "✔️ Deletions approved. Commit allowed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "🚫 Commit blocked to prevent accidental deletions." -ForegroundColor Red
    exit 1
}
