param([int]$Port=8000)

Write-Host "Starting uvicorn..." -ForegroundColor Cyan
$svc = Start-Process python -ArgumentList @('-m','uvicorn','main:app','--port',"$Port") -PassThru
Start-Sleep 2

try {
  function J($r){ $r | ConvertTo-Json -Depth 5 }
  $base = "http://127.0.0.1:$Port"

  Write-Host "GET /sim/health" -ForegroundColor Yellow
  $h = Invoke-RestMethod "$base/sim/health"
  J $h

  Write-Host "GET /sim/quote" -ForegroundColor Yellow
  $q = Invoke-RestMethod "$base/sim/quote?col_in=8000&min_out_bps=150&twap_guard=true"
  J $q

  $tmp = Join-Path $env:TEMP ("colink-smoke-{0}" -f (Get-Random))
  Write-Host "POST /sim/sweep?outdir=$tmp" -ForegroundColor Yellow
  $s = Invoke-RestMethod "$base/sim/sweep?outdir=$([uri]::EscapeDataString($tmp))" -Method Post
  J $s
  Get-ChildItem $tmp
}
finally {
  Write-Host "Stopping uvicorn..." -ForegroundColor Cyan
  if ($svc) { Stop-Process -Id $svc.Id -Force -ErrorAction SilentlyContinue }
  # Fallback stop if needed
  Get-CimInstance Win32_Process -Filter 'Name="python.exe"' |
    Where-Object { $_.CommandLine -match 'uvicorn.*main:app' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
