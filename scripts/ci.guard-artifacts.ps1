Write-Host "======================================="
Write-Host "ðŸ“¦ ci.guard-artifacts â€” Artifact Guard"
Write-Host "=======================================`n"

# Required directories inside .artifacts
$requiredDirs = @(
    ".artifacts",
    ".artifacts\ci",
    ".artifacts\data",
    ".artifacts\bundles",
    ".artifacts\metrics",
    ".artifacts\plots",
    ".artifacts\runs"
)

# Required files
$requiredFiles = @(
    ".artifacts\index.html",
    ".artifacts\ci\ci_summary.json"
)

$missing = @()

Write-Host "ðŸ” Checking required artifact directories..."

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "âœ… OK: $dir"
    } else {
        Write-Host "âŒ Missing directory: $dir"
        $missing += $dir
    }
}

Write-Host "`nðŸ” Checking required artifact files..."

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "âœ… OK: $file"
    } else {
        Write-Host "âŒ Missing file: $file"
        $missing += $file
    }
}

Write-Host "`n--------------------------------"
Write-Host "ðŸ“Š Artifact Guard Summary:"
Write-Host "--------------------------------"

if ($missing.Count -eq 0) {
    Write-Host "ðŸŸ¢ All artifact folders and files exist!"
} else {
    Write-Host "ðŸŸ¥ Missing artifacts detected:"
    $missing | ForEach-Object { Write-Host "   â†’ $_" }
    exit 1
}

Write-Host "ci.guard-artifacts completed."

