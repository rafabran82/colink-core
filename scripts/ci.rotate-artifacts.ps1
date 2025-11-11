# --- CI artifact rotation & cleanup ---
param (
    [string]$DataDir = ".artifacts\data",
    [int]$Keep = 100,
    [switch]$DryRun
)

if (-not (Test-Path $DataDir)) {
    Write-Warning "⚠️ Data directory not found: $DataDir"
    return
}

$dirs = Get-ChildItem -Path $DataDir -Directory | Sort-Object LastWriteTime -Descending
$total = $dirs.Count

if ($total -le $Keep) {
    Write-Host "✅ Nothing to rotate ($total runs, keep=$Keep)." -ForegroundColor Green
    return
}

$remove = $dirs | Select-Object -Skip $Keep
Write-Host "🧹 Rotating artifacts: keeping newest $Keep of $total" -ForegroundColor Cyan

foreach ($d in $remove) {
    if ($DryRun) {
        Write-Host "Would remove: $($d.FullName)"
    } else {
        try {
            Remove-Item -Recurse -Force -Path $d.FullName
            Write-Host "🗑️  Removed: $($d.Name)" -ForegroundColor DarkGray
        } catch {
            Write-Warning "Failed to remove $($d.FullName): $($_.Exception.Message)"
        }
    }
}

Write-Host "✅ Artifact rotation complete." -ForegroundColor Green
