Param(
    [switch]$FailOnIssues
)

Write-Host "🔎 EWS-ROUTE-CHECK running..." -ForegroundColor Cyan

$routesDir = "colink_core/api/routes"
$issues = @()

# 1) Route decorator regex
$routePattern = '@router\.(get|post|put|delete|patch)\("([^"]+)"'

# 2) Collect routes
$routeMap = @{}
Get-ChildItem -Path $routesDir -Filter *.py -File | ForEach-Object {

    $file = $_.FullName
    $content = Get-Content $file -Raw

    # Sanity: ensure APIRouter exists
    if ($content -notmatch "APIRouter") {
        $issues += "⚠️  $($_.Name): missing 'APIRouter' definition"
    }

    # Extract route decorators
    $matches = [regex]::Matches($content, $routePattern)

    foreach ($m in $matches) {
        $method = $m.Groups[1].Value.ToUpper()
        $path   = $m.Groups[2].Value

        # Normalize duplicates
        $key = "$method $path"
        if (-not $routeMap.ContainsKey($key)) {
            $routeMap[$key] = @()
        }
        $routeMap[$key] += $_.Name
    }
}

# 3) Detect duplicates
Write-Host ""
Write-Host "🔍 Checking for duplicate routes..." -ForegroundColor Yellow

foreach ($k in $routeMap.Keys) {
    $list = $routeMap[$k]
    if ($list.Count -gt 1) {
        $issues += "❌ Duplicate route: $k  →  $($list -join ', ')"
    }
}

# 4) Detect malformed paths
foreach ($k in $routeMap.Keys) {
    if ($k -notmatch '^([A-Z]+)\s/.*') {
        $issues += "⚠️ Malformed route path in: $k"
    }
}

# 5) Report
if ($issues.Count -eq 0) {
    Write-Host "✅ No route issues detected." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "❗ ROUTE ISSUES FOUND:" -ForegroundColor Red
$issues | ForEach-Object { Write-Host "  $_" }

if ($FailOnIssues) {
    Write-Host "⛔ Failing due to issues (FailOnIssues enabled)." -ForegroundColor Red
    exit 1
} else {
    Write-Host "⚠️  (Use -FailOnIssues to stop CI on these problems.)"
}

exit 0
