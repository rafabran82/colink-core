Write-Host "=========================================="
Write-Host "ðŸ” ci.guard-syntax â€” PowerShell Syntax Guard"
Write-Host "==========================================`n"

# Collect all PowerShell scripts
$psFiles = Get-ChildItem -Recurse -Filter *.ps1 -ErrorAction SilentlyContinue

if (-not $psFiles) {
    Write-Host "âš ï¸ No PowerShell files found â€” skipping syntax guard."
    exit 0
}

$errors = @()

foreach ($f in $psFiles) {
    Write-Host "ðŸ” Checking syntax: $($f.FullName)"

    $cmd = "Get-Command -Name `"$($f.FullName)`" -ErrorAction Stop"
    $out = powershell -noprofile -command $cmd 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "âŒ Syntax error in: $($f.FullName)"
        Write-Host "    â†’ $out"
        $errors += $f.FullName
    } else {
        Write-Host "âœ… OK: $($f.Name)"
    }
}

Write-Host "`n---------------------------"
Write-Host "ðŸ“Š Syntax Guard Summary:"
Write-Host "---------------------------"

if ($errors.Count -eq 0) {
    Write-Host "ðŸŸ¢ All PowerShell scripts are syntactically valid!"
} else {
    Write-Host "ðŸŸ¥ Errors found in the following scripts:"
    $errors | ForEach-Object { Write-Host "   â†’ $_" }
    exit 1
}

Write-Host "ci.guard-syntax completed."

