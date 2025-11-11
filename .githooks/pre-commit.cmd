@echo off
REM Launch PowerShell hook (prefer pwsh, fallback to Windows PowerShell)
where pwsh >NUL 2>&1
IF %ERRORLEVEL%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0pre-commit.ps1"
  exit /b %ERRORLEVEL%
) ELSE (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pre-commit.ps1"
  exit /b %ERRORLEVEL%
)
