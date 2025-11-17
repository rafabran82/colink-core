Write-Host "🔍 Running EWS-PREFIX-CHECK..." -ForegroundColor Yellow

$issues = 0

# Collect all Python route files
$routeFiles = @(Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue)

if ($routeFiles.Count -eq 0) {
    Write-Host "⚠️ No Python files found — skipping prefix check." -ForegroundColor DarkYellow
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
                Write-Host "🟥 Invalid route prefix in: $($f.FullName)" -ForegroundColor Red
                Write-Host "     → $l"
                $issues++
            }
        }
    }
}

if ($issues -eq 0) {
    Write-Host "🟢 Prefix check completed — no issues found." -ForegroundColor Green
} else {
    Write-Host "🟧 Prefix check completed — $issues issue(s) found." -ForegroundColor DarkYellow
}
