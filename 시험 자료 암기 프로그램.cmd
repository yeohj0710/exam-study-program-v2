@echo off
chcp 65001 >nul
setlocal

set "LAUNCHER="
for /d %%D in ("%~dp0*") do (
  if exist "%%~fD\launcher\start-studyforge.ps1" set "LAUNCHER=%%~fD\launcher\start-studyforge.ps1"
)

if not defined LAUNCHER (
  echo Launcher was not found.
  echo Re-download or unzip the repository, then try again.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER%"
if errorlevel 1 pause
