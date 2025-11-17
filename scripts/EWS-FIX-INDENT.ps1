Write-Host "🔧 Running EWS-FIX-INDENT..." -ForegroundColor Yellow

$files = Get-ChildItem -Recurse -Filter *.py
foreach ($f in $files) {
    $c = Get-Content $f.FullName
    $fixed = $c -replace "^\t+", "    "
    Set-Content -Path $f.FullName -Value $fixed
}
Write-Host "🟢 Indentation normalized." -ForegroundColor Green
