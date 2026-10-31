@echo off
cd /d "K:\Fluxgroup\FluxGroup" || exit /b 1
set PYTHONIOENCODING=utf-8
python Tools\fleet\planner.py --node bm-c --root "K:\Fluxgroup\FluxGroup" >> cph4\fleet\plans\planner_task.log 2>&1
exit /b 0
