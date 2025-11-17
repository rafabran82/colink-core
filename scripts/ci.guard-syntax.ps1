Write-Host "=========================================="
Write-Host "🔍 ci.guard-syntax — PowerShell Syntax Guard"
Write-Host "==========================================`n"

# Collect all PowerShell scripts
$psFiles = Get-ChildItem -Recurse -Filter *.ps1 -ErrorAction SilentlyContinue

if (-not $psFiles) {
    Write-Host "⚠️ No PowerShell files found — skipping syntax guard."
    exit 0
}

$errors = @()

foreach ($f in $psFiles) {
    Write-Host "🔍 Checking syntax: $($f.FullName)"

    $cmd = "Get-Command -Name `"$($f.FullName)`" -ErrorAction Stop"
    $out = powershell -noprofile -command $cmd 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Syntax error in: $($f.FullName)"
        Write-Host "    → $out"
        $errors += $f.FullName
    } else {
        Write-Host "✅ OK: $($f.Name)"
    }
}

Write-Host "`n---------------------------"
Write-Host "📊 Syntax Guard Summary:"
Write-Host "---------------------------"

if ($errors.Count -eq 0) {
    Write-Host "🟢 All PowerShell scripts are syntactically valid!"
} else {
    Write-Host "🟥 Errors found in the following scripts:"
    $errors | ForEach-Object { Write-Host "   → $_" }
    exit 1
}

Write-Host "ci.guard-syntax completed."
