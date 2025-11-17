Write-Host "🧹 Running EWS-FORMAT-CHECK..."

# Only scan REAL project source files
$files = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -in ".ps1", ".py", ".ts", ".js" -and
        $_.FullName -notmatch "backup" -and
        $_.FullName -notmatch "bak" -and
        $_.FullName -notmatch "Local-CI" -and
        $_.FullName -notmatch "\.pyc$" -and
        $_.FullName -notmatch "\.artifacts" -and
        $_.FullName -notmatch "__pycache__"
    }

$issues = 0

foreach ($f in $files) {
    $lines = Get-Content $f.FullName
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match "\s+$") {
            Write-Host "🟥 Trailing whitespace: $($f.Name):$($i+1)"
            $issues++
        }
    }
}

if ($issues -eq 0) {
    Write-Host "🟢 Formatting clean — no issues found."
} else {
    Write-Host "🟧 Formatting issues detected: $issues lines with trailing whitespace."
}
