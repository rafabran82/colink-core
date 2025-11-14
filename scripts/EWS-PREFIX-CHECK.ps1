Param(
    [switch]$FailOnIssues
)

Write-Host "🔎 EWS-PREFIX-CHECK running..." -ForegroundColor Cyan

$routesDir = "colink_core/api/routes"
$mainFile  = "colink_core/api/main.py"
$issues    = @()

# ---------------------------------------------------------
# 1) Detect global prefix used in main.py
# ---------------------------------------------------------
if (-not (Test-Path $mainFile)) {
    Write-Host "❌ Cannot find main.py at $mainFile" -ForegroundColor Red
    exit 1
}

$mainText = Get-Content $mainFile -Raw
$prefixMatches = [regex]::Matches($mainText, 'include_router\([^,]+,\s*prefix\s*=\s*"([^"]+)"')

$globalPrefixes = $prefixMatches.Groups[1].Value | Sort-Object -Unique

if ($globalPrefixes.Count -eq 0) {
    Write-Host "⚠️  No prefixes found in main.py — cannot validate prefix consistency."
} else {
    Write-Host "🌐 Global prefix(es) detected in main.py: $($globalPrefixes -join ', ')"
}

# ---------------------------------------------------------
# 2) Scan each router file for prefix usage
# ---------------------------------------------------------
Write-Host ""
Write-Host "🔍 Scanning router files for prefix consistency..." -ForegroundColor Yellow

$prefixPattern = '@router\.(get|post|put|delete|patch)\("([^"]+)"'

Get-ChildItem -Path $routesDir -Filter *.py -File | ForEach-Object {
    $file = $_
    $content = Get-Content $file.FullName -Raw

    # Extract all routes
    $matches = [regex]::Matches($content, $prefixPattern)

    if ($matches.Count -eq 0) {
        Write-Host "ℹ️  No routes in $($file.Name) — skipping."
        return
    }

    # Check each route’s path
    foreach ($m in $matches) {
        $method = $m.Groups[1].Value.ToUpper()
        $path   = $m.Groups[2].Value

        # 1) All paths must start with "/"
        if ($path -notmatch '^/') {
            $issues += "❌ $($file.Name): $method '$path' — path must start with '/'"
        }

        # 2) Check against global prefixes
        foreach ($gp in $globalPrefixes) {
            if ($gp -eq "/api") {
                # Expect /api/*? No — dashboard API registers its own path
                # So just warn if route starts with /api/api
                if ($path -match '^/api/api') {
                    $issues += "⚠️  $($file.Name): $method '$path' — double '/api' prefix detected"
                }
            }
        }
    }
}

# ---------------------------------------------------------
# 3) Report
# ---------------------------------------------------------
Write-Host ""
if ($issues.Count -eq 0) {
    Write-Host "✅ No prefix issues detected." -ForegroundColor Green
    exit 0
}

Write-Host "❗ PREFIX ISSUES FOUND:" -ForegroundColor Red
$issues | ForEach-Object { Write-Host "  $_" }

if ($FailOnIssues) {
    Write-Host "⛔ Failing due to prefix errors (FailOnIssues enabled)." -ForegroundColor Red
    exit 1
}

Write-Host "⚠️  (Use -FailOnIssues to stop CI on prefix inconsistencies.)"
exit 0
