param(
    [switch]$FailOnIssues
)

# Detect repo root via git
$repo = git rev-parse --show-toplevel 2>$null
if (-not $repo) {
    Write-Error "❌ EWS-DUP-SCAN: not inside a git repository."
    exit 1
}
Set-Location $repo

$issueCount = 0

Write-Host "🔍 EWS-DUP-SCAN running in: $repo" -ForegroundColor Cyan

# ============================
# 1) Duplicate Python modules
# ============================
$moduleRoots = @(
    "colink_core\api\routes",
    "routes",
    "colink_core\sim"
) | ForEach-Object { Join-Path $repo $_ } | Where-Object { Test-Path $_ }

$pyFiles = @()
foreach ($root in $moduleRoots) {
    $pyFiles += Get-ChildItem -Path $root -Recurse -Filter *.py -File
}

if ($pyFiles.Count -gt 0) {
    $groups = $pyFiles | Group-Object BaseName | Where-Object { $_.Count -gt 1 }

    # Names that are commonly duplicated and usually safe
    $ignoreNames = @(
        "__init__", "__main__", "conftest",
        "test_amm", "test_limits", "test_router",
        "test_risk_guard", "test_api_sim",
        "run"   # allow run + mvp/run etc. without screaming
    )

    $dups = $groups | Where-Object { $ignoreNames -notcontains $_.Name }

    if ($dups) {
        Write-Host ""
        Write-Host "⚠️  Potential duplicate Python modules found:" -ForegroundColor Yellow
        foreach ($g in $dups) {
            Write-Host "  - [$($g.Name)]" -ForegroundColor Yellow
            foreach ($f in $g.Group) {
                $rel = $f.FullName.Substring($repo.Length + 1)
                Write-Host "      $rel"
            }
        }
        $issueCount += $dups.Count
    } else {
        Write-Host "✅ No suspicious duplicate Python modules." -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️ No Python files found under module roots." -ForegroundColor DarkGray
}

# ======================================
# 2) Duplicate FastAPI routes (method+path)
# ======================================
$routeDir = Join-Path $repo "colink_core\api\routes"

if (Test-Path $routeDir) {
    $routeDefs = @()

    Get-ChildItem -Path $routeDir -Filter *.py -File | ForEach-Object {
        $file = $_

        # Read file safely (empty file => skip)
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        if ([string]::IsNullOrWhiteSpace($content)) {
            $rel = $file.FullName.Substring($repo.Length + 1)
            Write-Host "ℹ️ Skipping empty or unreadable file: $rel" -ForegroundColor DarkGray
        }
        else {
            # Match @router.get("/path"), @router.post("/path"), etc.
            $pattern = '@router\.(get|post|put|patch|delete)\("([^"]+)"'
            $matches = [System.Text.RegularExpressions.Regex]::Matches($content, $pattern)

            foreach ($m in $matches) {
                $method = $m.Groups[1].Value.ToUpperInvariant()
                $path   = $m.Groups[2].Value
                $routeDefs += [PSCustomObject]@{
                    Method = $method
                    Path   = $path
                    File   = $file.FullName.Substring($repo.Length + 1)
                }
            }
        }
    }

    if ($routeDefs.Count -gt 0) {
        $dupRoutes = $routeDefs | Group-Object Method, Path | Where-Object { $_.Count -gt 1 }

        if ($dupRoutes) {
            Write-Host ""
            Write-Host "⚠️  Duplicate FastAPI routes detected:" -ForegroundColor Yellow
            foreach ($g in $dupRoutes) {
                Write-Host "  - $($g.Name)" -ForegroundColor Yellow
                foreach ($r in $g.Group) {
                    Write-Host "      $($r.File)"
                }
            }
            $issueCount += $dupRoutes.Count
        } else {
            Write-Host "✅ No duplicate FastAPI routes." -ForegroundColor Green
        }
    } else {
        Write-Host "ℹ️ No router.*(...) decorators found in colink_core\\api\\routes." -ForegroundColor DarkGray
    }
} else {
    Write-Host "ℹ️ Routes directory not found: $routeDir" -ForegroundColor DarkGray
}

# ============================
# Summary / Exit behavior
# ============================
Write-Host ""

if ($issueCount -gt 0) {
    Write-Host "EWS-DUP-SCAN: $issueCount issue group(s) found." -ForegroundColor Yellow

    if ($FailOnIssues) {
        Write-Host "Failing with exit code 1 because -FailOnIssues was set." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "Run again with -FailOnIssues to make CI fail on these." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "✅ EWS-DUP-SCAN: no issues detected." -ForegroundColor Green
}
