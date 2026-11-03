@echo off
chcp 65001 >nul 2>&1
:: One-click launcher: bm-b performance release to maximum (reversible).
:: Order: OB-20261103-1240-BMB-PERF-MAX
:: Needs admin -> this script re-launches itself elevated (one UAC prompt).

net session >nul 2>&1
if errorlevel 1 (
  echo Requesting administrator rights...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Running performance release script...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Tools\fleet\win\perf_max.ps1"
echo.
echo Done. Log is under cph4\fleet\queue-receipts\perf-max-*.log
pause