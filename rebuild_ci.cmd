@echo off
setlocal
pushd %~dp0
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "scripts\ci.rebuild-and-refresh.ps1"
popd
endlocal
