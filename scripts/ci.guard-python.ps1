Write-Host "======================================="
Write-Host "ðŸ§ª ci.guard-python â€” Python Syntax Guard"
Write-Host "=======================================`n"

# Find all Python files in the repo
$pyFiles = Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue

if (-not $pyFiles) {
    Write-Host "âš ï¸ No Python files found â€” skipping Python guard."
    Write-Host "`nðŸŸ¢ ci.guard-python: All checks complete."
    exit 0
}

$errors = @()

foreach ($f in $pyFiles) {
    Write-Host "ðŸ” Checking: $($f.FullName)"

    $out = & python -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "âŒ Syntax error in: $($f.FullName)"
        Write-Host "    â†’ $out"
        $errors += $f.FullName
    } else {
        Write-Host "âœ… OK: $($f.Name)"
    }
}

Write-Host "`n---------------------------"
Write-Host "ðŸ“Š Python Guard Summary:"
Write-Host "---------------------------"

if ($errors.Count -eq 0) {
    Write-Host "ðŸŸ¢ No syntax errors found in Python scripts!"
    Write-Host "ci.guard-python completed successfully."
} else {
    Write-Host "ðŸŸ¥ Errors detected in the following files:"
    $errors | ForEach-Object { Write-Host "   â†’ $_" }
    exit 1
}

