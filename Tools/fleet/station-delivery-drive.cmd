@echo off
REM delivery station self-drive (one round). Station identity MUST be set: without it the
REM tools refuse to run (rc=2) instead of silently acting as control.
set FLEET_STATION=delivery
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d C:\Users\sjs20\Desktop\FluxGroup
"C:\Users\sjs20\AppData\Local\Programs\Python\Python314\python.exe" Tools\fleet\station_drive.py --station delivery --once --run-limit 6 >> "C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\rt\delivery\drive.log" 2>&1
exit /b %ERRORLEVEL%
