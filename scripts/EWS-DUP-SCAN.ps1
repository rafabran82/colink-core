Write-Host "🔍 Running EWS-DUP-SCAN..." -ForegroundColor Yellow

$issues = 0

# -----------------------------
# 1) Scan for duplicate Python modules
# -----------------------------
$pyFiles = @(Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue)

if ($pyFiles.Count -eq 0) {
    Write-Host "⚠️ No Python files found — skipping Python duplicate module scan." -ForegroundColor DarkYellow
} else {
    $moduleNames = @{}

    foreach ($file in $pyFiles) {
        $base = $file.BaseName
        if ($moduleNames.ContainsKey($base)) {
            Write-Host "🟥 Duplicate Python module found: $base" -ForegroundColor Red
            $issues++
        } else {
            $moduleNames[$base] = $file.FullName
        }
    }
}

# -----------------------------
# 2) Scan for duplicate FastAPI route decorators
# -----------------------------
$routeFiles = @(Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue)

if ($routeFiles.Count -eq 0) {
    Write-Host "⚠️ No Python files found for route scan — skipping duplicate route check." -ForegroundColor DarkYellow
} else {
    $routeLines = @()

    foreach ($f in $routeFiles) {
        $matches = @(Select-String -Path $f.FullName -Pattern "@router" -ErrorAction SilentlyContinue)
        if ($matches.Count -gt 0) {
            $routeLines += $matches
        }
    }

    $routeMap = @{}

    foreach ($r in $routeLines) {
        $routeKey = $r.Line.Trim()

        if ($routeMap.ContainsKey($routeKey)) {
            Write-Host "🟥 Duplicate FastAPI route: $routeKey" -ForegroundColor Red
            $issues++
        } else {
            $routeMap[$routeKey] = 1
        }
    }
}

# -----------------------------
# RESULT
# -----------------------------
if ($issues -eq 0) {
    Write-Host "🟢 EWS-DUP-SCAN: No issues detected." -ForegroundColor Green
} else {
    Write-Host "🟧 EWS-DUP-SCAN completed with $issues issue(s)." -ForegroundColor DarkYellow
}
