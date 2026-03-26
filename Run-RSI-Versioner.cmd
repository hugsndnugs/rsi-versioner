@echo off
setlocal
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\Install-or-Run.ps1"
if errorlevel 1 (
  echo.
  echo Failed to install or launch RSI Versioner.
  pause
)
