param(
    [Parameter(Mandatory=$true)]
    [string]$RunDir
)

Write-Host "▶ Running Delta Engine (sim_compute_delta.ps1)..." -ForegroundColor Cyan

# --- Validate run dir ---------------------------------------------------------
if (-not (Test-Path $RunDir)) {
    Write-Host "❌ Run directory not found: $RunDir" -ForegroundColor Red
    exit 1
}

$before = Join-Path $RunDir "before.json"
$after  = Join-Path $RunDir "after.json"

if (-not (Test-Path $before)) {
    Write-Host "❌ Missing before.json in run dir" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $after)) {
    Write-Host "❌ Missing after.json in run dir" -ForegroundColor Red
    exit 1
}

# --- Load JSON ----------------------------------------------------------------
$beforeObj = Get-Content $before -Raw | ConvertFrom-Json
$afterObj  = Get-Content $after  -Raw | ConvertFrom-Json

# Convert to dictionaries for comparison
$beforeDict = @{}
$afterDict  = @{}
$beforeObj.PSObject.Properties | ForEach-Object { $beforeDict[$_.Name] = $_.Value }
$afterObj.PSObject.Properties  | ForEach-Object { $afterDict[$_.Name]  = $_.Value }

# --- Compute Delta -------------------------------------------------------------
$delta = [ordered]@{
    added    = @{}
    removed  = @{}
    changed  = @{}
}

foreach ($key in $afterDict.Keys) {
    if (-not $beforeDict.ContainsKey($key)) {
        $delta.added[$key] = $afterDict[$key]
    }
}

foreach ($key in $beforeDict.Keys) {
    if (-not $afterDict.ContainsKey($key)) {
        $delta.removed[$key] = $beforeDict[$key]
    }
}

foreach ($key in $beforeDict.Keys) {
    if ($afterDict.ContainsKey($key)) {
        if ($beforeDict[$key] -ne $afterDict[$key]) {
            $delta.changed[$key] = @{
                before = $beforeDict[$key]
                after  = $afterDict[$key]
            }
        }
    }
}

$outFile = Join-Path $RunDir "delta.json"
$delta | ConvertTo-Json -Depth 10 | Set-Content -Path $outFile -Encoding utf8

Write-Host ""
Write-Host "📊 DELTA SUMMARY" -ForegroundColor Cyan
Write-Host "   ➕ Added:    $($delta.added.Keys.Count)"
Write-Host "   ➖ Removed:  $($delta.removed.Keys.Count)"
Write-Host "   🔄 Changed:  $($delta.changed.Keys.Count)"
Write-Host ""

if ($delta.changed.Keys.Count -eq 0 -and
    $delta.added.Keys.Count -eq 0 -and
    $delta.removed.Keys.Count -eq 0) {
    Write-Host "🟢 No changes detected (idempotent)" -ForegroundColor Green
}
else {
    Write-Host "🟡 Delta detected – see delta.json" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🟢 Delta Engine Complete"
