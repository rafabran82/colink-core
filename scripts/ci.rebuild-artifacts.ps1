Write-Host "====================================="
Write-Host "🔧 ci.rebuild-artifacts — Rebuilder"
Write-Host "=====================================`n"

$dirs = @(
    ".artifacts",
    ".artifacts\ci",
    ".artifacts\data",
    ".artifacts\bundles",
    ".artifacts\metrics",
    ".artifacts\plots",
    ".artifacts\runs"
)

$files = @(
    ".artifacts\index.html",
    ".artifacts\ci\ci_summary.json"
)

Write-Host "📂 Ensuring directory structure..."

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
        Write-Host "✅ Created: $d"
    } else {
        Write-Host "🟦 Exists: $d"
    }

    # Drop a .gitkeep so Git tracks empty dirs
    $gitkeep = Join-Path $d ".gitkeep"
    if (-not (Test-Path $gitkeep)) {
        Set-Content -Path $gitkeep -Value "" -Encoding utf8
        Write-Host "   → added .gitkeep"
    }
}

Write-Host "`n📄 Ensuring required files..."

foreach ($f in $files) {
    if (-not (Test-Path $f)) {
        if ($f -like "*.html") {
            Set-Content -Path $f -Value "<!-- placeholder index -->" -Encoding utf8
        } elseif ($f -like "*.json") {
            Set-Content -Path $f -Value "{}" -Encoding utf8
        }
        Write-Host "✅ Created: $f"
    } else {
        Write-Host "🟦 Exists: $f"
    }
}

Write-Host "`n🎉 Artifact rebuild complete!"
Write-Host "🟢 All required artifact directories and files now exist."
