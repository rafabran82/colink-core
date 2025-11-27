param(
    [string]$RunDir
)

if (-not $RunDir) {
    Write-Host "❌ Missing -RunDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $RunDir)) {
    Write-Host "❌ Run directory does not exist: $RunDir" -ForegroundColor Red
    exit 1
}

$output = Join-Path $RunDir "sim_output.json"
$meta   = Join-Path $RunDir "meta.json"

$ok = $true

if (-not (Test-Path $output)) {
    Write-Host "❌ sim_output.json missing" -ForegroundColor Red
    $ok = $false
} else {
    Write-Host "🟢 sim_output.json OK" -ForegroundColor Green
}

if (-not (Test-Path $meta)) {
    Write-Host "❌ meta.json missing" -ForegroundColor Red
    $ok = $false
} else {
    Write-Host "🟢 meta.json OK" -ForegroundColor Green
}

if ($ok) {
    Write-Host "🟢 Simulation run verified" -ForegroundColor Green
} else {
    Write-Host "🟠 Simulation run incomplete" -ForegroundColor Yellow
}
