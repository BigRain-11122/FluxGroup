# Runs a PowerShell script through the hidden chain (console-less).
@echo off
if "%~1"=="" exit /b 2
powershell -NoProfile -ExecutionPolicy Bypass %*
exit /b %ERRORLEVEL%