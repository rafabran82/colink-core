param(
    [string[]]$Files
)

Write-Host "🛠️  Running EWS-FIX-INDENT..." -ForegroundColor Cyan

$results = @()

foreach ($f in $Files) {
    if (-not (Test-Path $f)) {
        Write-Host "   ⚠️  Skipping missing file: $f" -ForegroundColor Yellow
        continue
    }

    Write-Host "   → Fixing: $f" -ForegroundColor Yellow

    $backup = "$f.bak"
    Copy-Item $f $backup -Force

    $original = Get-Content $f -Raw
    $fixed    = $original -replace "`t", "    "

    if ($original -ne $fixed) {
        Set-Content -Path $f -Value $fixed -Encoding utf8
        Write-Host "      ✔ Tabs → spaces" -ForegroundColor Green
        $results += $f
    } else {
        Write-Host "      ✔ Already clean (no tabs found)" -ForegroundColor DarkGray
    }
}

Write-Host "`n⭐ EWS-FIX-INDENT completed" -ForegroundColor Cyan
Write-Host "   Fixed: $($results.Count) file(s)" -ForegroundColor Green

return $results
