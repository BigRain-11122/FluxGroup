@echo off
REM delivery station patrol agent (one round). Reports findings only; never changes cards.
set FLEET_STATION=delivery
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d C:\Users\sjs20\Desktop\FluxGroup
"C:\Users\sjs20\AppData\Local\Programs\Python\Python314\python.exe" Tools\fleet\station_agent.py --station delivery --once >> "C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\rt\delivery\agent.log" 2>&1
exit /b %ERRORLEVEL%
