Write-Host "🔍 Running EWS-ROUTE-CHECK..." -ForegroundColor Yellow

# Find all Python files
$pyFiles = @(Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue)

if ($pyFiles.Count -eq 0) {
    Write-Host "⚠️ No Python files found — skipping route check." -ForegroundColor DarkYellow
    return
}

$issues = 0

foreach ($file in $pyFiles) {
    $data = Get-Content $file.FullName -ErrorAction SilentlyContinue

    foreach ($line in $data) {

        # Match valid route definitions safely
        # Example: @router.get("/accounts")
        if ($line -match '@router\.(get|post|put|delete)\("([^"]+)"\)') {

            $route = $Matches[2]

            # Route must start with "/"
            if ($route -notmatch '^(\/[a-z0-9_\-\/]*)$') {
                Write-Host "🟥 Invalid route in $($file.FullName)" -ForegroundColor Red
                Write-Host "     → $line"
                $issues++
            }
        }
    }
}

if ($issues -eq 0) {
    Write-Host "🟢 Route check completed — no issues found." -ForegroundColor Green
} else {
    Write-Host "🟧 Route check completed — $issues issue(s) found." -ForegroundColor DarkYellow
}
