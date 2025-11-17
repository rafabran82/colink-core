Write-Host "======================================="
Write-Host "🧪 ci.guard-python — Python Syntax Guard"
Write-Host "=======================================`n"

# Find all Python files in the repo
$pyFiles = Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue

if (-not $pyFiles) {
    Write-Host "⚠️ No Python files found — skipping Python guard."
    Write-Host "`n🟢 ci.guard-python: All checks complete."
    exit 0
}

$errors = @()

foreach ($f in $pyFiles) {
    Write-Host "🔍 Checking: $($f.FullName)"

    $out = & python -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Syntax error in: $($f.FullName)"
        Write-Host "    → $out"
        $errors += $f.FullName
    } else {
        Write-Host "✅ OK: $($f.Name)"
    }
}

Write-Host "`n---------------------------"
Write-Host "📊 Python Guard Summary:"
Write-Host "---------------------------"

if ($errors.Count -eq 0) {
    Write-Host "🟢 No syntax errors found in Python scripts!"
    Write-Host "ci.guard-python completed successfully."
} else {
    Write-Host "🟥 Errors detected in the following files:"
    $errors | ForEach-Object { Write-Host "   → $_" }
    exit 1
}
