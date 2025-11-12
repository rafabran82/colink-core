@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
@echo off
setlocal
pushd %~dp0
REM Only call the PS rebuild if it exists; otherwise exit 0 quietly
if exist "scripts\ci.rebuild.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\ci.rebuild.ps1"
) else (
  REM no-op
)
popd
endlocal



