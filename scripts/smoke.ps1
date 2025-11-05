# scripts/smoke.ps1
$ErrorActionPreference = 'Stop'
$base = "http://127.0.0.1:8010"
Write-Host "Health:" -ForegroundColor Cyan
Invoke-RestMethod "$base/sim/health" | Format-List

Write-Host "`nQuote:" -ForegroundColor Cyan
Invoke-RestMethod "$base/sim/quote?col_in=8000&min_out_bps=150&twap_guard=true" | Format-List

Write-Host "`nSweep:" -ForegroundColor Cyan
$tmp = Join-Path $env:TEMP "colink-smoke-$(Get-Random)"
$r = Invoke-RestMethod -Uri ("$base/sim/sweep?outdir=" + [uri]::EscapeDataString($tmp)) -Method Post
$r | Format-List
Get-ChildItem $tmp
