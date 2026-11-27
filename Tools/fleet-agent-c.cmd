@echo off
cd /d "K:\Fluxgroup\FluxGroup" || exit /b 1
set PYTHONIOENCODING=utf-8
python Tools\fleet\fleet_agent.py --node bm-c --root "K:\Fluxgroup\FluxGroup" --once >> cph4\fleet\queue-receipts\_agent_task.log 2>&1
exit /b %ERRORLEVEL%
