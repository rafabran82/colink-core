@echo off
@echo off
@echo off
setlocal
pushd %~dp0
pwsh -NoProfile -ExecutionPolicy Bypass -File "scripts\sim.run.ps1"
if exist ".artifacts\index.html" start "" ".artifacts\index.html"
popd
endlocal
