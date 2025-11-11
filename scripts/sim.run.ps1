$ErrorActionPreference = "Stop"

# --- Sim Run Stub (Phase 3, Step 1) ---
$repo   = (git rev-parse --show-toplevel)
Set-Location $repo

$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $repo ".artifacts\data\$stamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host "🧩 Sim run started: $stamp"
Write-Host "📂 Output folder: $outDir"

# For now, just write a tiny meta JSON
$meta = @{
    run_id     = $stamp
    created_at = (Get-Date).ToString("s")
    note       = "Phase3-Step1 stub run"
}
$meta | ConvertTo-Json | Set-Content (Join-Path $outDir "run_meta.json") -Encoding utf8

Write-Host "✅ Created run_meta.json"
Write-Host "✅ Dashboard refreshed (simulated) at .artifacts\index.html"
