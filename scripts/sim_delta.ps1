param(
    [string]$Before,
    [string]$After,
    [string]$Out = "sim_delta.json"
)

Write-Host "▶ Computing simulation deltas..." -ForegroundColor Cyan

if (-not (Test-Path $Before)) {
    Write-Host "❌ Missing BEFORE state: $Before" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $After)) {
    Write-Host "❌ Missing AFTER state: $After" -ForegroundColor Red
    exit 1
}

$prev = Get-Content $Before | ConvertFrom-Json
$next = Get-Content $After | ConvertFrom-Json

$delta = @{}

# Compare top-level numeric fields
foreach ($key in $prev.PSObject.Properties.Name) {
    if ($prev.$key -is [double] -or $prev.$key -is [int]) {
        $delta[$key] = $next.$key - $prev.$key
    }
}

# Write delta file
$delta | ConvertTo-Json -Depth 10 | Set-Content $Out -Encoding utf8

Write-Host "🟢 Delta analysis complete" -ForegroundColor Green
Write-Host "📦 Output: $Out"
