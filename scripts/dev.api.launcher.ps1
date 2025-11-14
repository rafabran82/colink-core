# COLINK API backend dev launcher

Set-Location "C:\Users\sk8br\Desktop\colink-core"

Write-Host "Starting COLINK API backend..." -ForegroundColor Cyan
Write-Host ""

# TODO: Adjust this command if your API entrypoint is different.
# Common pattern:
#   uvicorn colink_core.api.main:app --reload --host 127.0.0.1 --port 8000

uvicorn colink_core.api.main:app --reload --host 127.0.0.1 --port 8000
