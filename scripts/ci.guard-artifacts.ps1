Write-Host "======================================="
Write-Host "📦 ci.guard-artifacts — Artifact Guard"
Write-Host "=======================================`n"

# Required directories inside .artifacts
$requiredDirs = @(
    ".artifacts",
    ".artifacts\ci",
    ".artifacts\data",
    ".artifacts\bundles",
    ".artifacts\metrics",
    ".artifacts\plots",
    ".artifacts\runs"
)

# Required files
$requiredFiles = @(
    ".artifacts\index.html",
    ".artifacts\ci\ci_summary.json"
)

$missing = @()

Write-Host "🔍 Checking required artifact directories..."

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ OK: $dir"
    } else {
        Write-Host "❌ Missing directory: $dir"
        $missing += $dir
    }
}

Write-Host "`n🔍 Checking required artifact files..."

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ OK: $file"
    } else {
        Write-Host "❌ Missing file: $file"
        $missing += $file
    }
}

Write-Host "`n--------------------------------"
Write-Host "📊 Artifact Guard Summary:"
Write-Host "--------------------------------"

if ($missing.Count -eq 0) {
    Write-Host "🟢 All artifact folders and files exist!"
} else {
    Write-Host "🟥 Missing artifacts detected:"
    $missing | ForEach-Object { Write-Host "   → $_" }
    exit 1
}

Write-Host "ci.guard-artifacts completed."
