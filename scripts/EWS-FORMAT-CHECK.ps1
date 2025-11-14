param(
    [string[]]$Extensions = @("*.py", "*.ps1", "*.psm1")
)

Write-Host "   (EWS-FORMAT-CHECK) scanning formatting (trailing spaces / tabs)..." -ForegroundColor DarkGray

$root = Get-Location

# Collect candidate files (project code only, ignore tooling/venv/git/node_modules/backup CI scripts)
$files = Get-ChildItem -Path $root -Recurse -File -Include $Extensions -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notlike "*\.venv\*" -and
        $_.FullName -notlike "*\.git\*"  -and
        $_.FullName -notlike "*node_modules*" -and
        $_.FullName -notlike "*scripts\Local-CI.backup*.ps1"
    }

$issues = @()

foreach ($f in $files) {
    try {
        $text = Get-Content -Path $f.FullName -Raw -ErrorAction Stop
    } catch {
        Write-Host "      ℹ️ Skipping unreadable file: $($f.FullName)" -ForegroundColor DarkYellow
        continue
    }

    $localIssues = @()

    # Trailing whitespace (spaces before end-of-line)
    if ($text -match " +`r?`n") {
        $localIssues += "trailing spaces"
    }

    # Tab characters
    if ($text -match "`t") {
        $localIssues += "tab characters"
    }

    if ($localIssues.Count -gt 0) {
        $issues += [PSCustomObject]@{
            File   = $f.FullName
            Issues = ($localIssues | Sort-Object -Unique) -join ", "
        }
    }
}

if ($issues.Count -gt 0) {
    Write-Host "   ❌ Formatting issues detected in the following files:" -ForegroundColor Red
    $issues |
        Sort-Object File -Unique |
        ForEach-Object {
            Write-Host "      $($_.File)  →  $($_.Issues)"
        }

    exit 1
}
else {
    Write-Host "   ✅ Formatting clean (no trailing spaces or tabs in project files)" -ForegroundColor Green
    exit 0
}
