Write-Host "ðŸ” Running EWS-PREFIX-CHECK..." -ForegroundColor Yellow

$issues = 0

# Collect all Python route files
$routeFiles = @(Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue)

if ($routeFiles.Count -eq 0) {
    Write-Host "âš ï¸ No Python files found â€” skipping prefix check." -ForegroundColor DarkYellow
    return
}

foreach ($f in $routeFiles) {

    $lines = @(Get-Content $f.FullName -ErrorAction SilentlyContinue)

    foreach ($l in $lines) {

        # Only evaluate decorator lines
        if ($l -match "@router\.(get|post|put|delete)") {

            # Check the route string
            # This enforces: must begin with "/something" AND all lowercase
            if ($l -notmatch '@router\.(get|post|put|delete)\("/[a-z0-9_\-]+' ) {
                Write-Host "ðŸŸ¥ Invalid route prefix in: $($f.FullName)" -ForegroundColor Red
                Write-Host "     â†’ $l"
                $issues++
            }
        }
    }
}

if ($issues -eq 0) {
    Write-Host "ðŸŸ¢ Prefix check completed â€” no issues found." -ForegroundColor Green
} else {
    Write-Host "ðŸŸ§ Prefix check completed â€” $issues issue(s) found." -ForegroundColor DarkYellow
}

