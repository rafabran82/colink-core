param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8011,
  [string]$Log = "debug"
)
$pidOnPort = (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess)
if ($pidOnPort) { taskkill /PID $pidOnPort /F | Out-Null }
.\.venv\Scripts\python.exe -m uvicorn main:app --host $BindHost --port $Port --log-level $Log
