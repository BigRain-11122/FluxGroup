@echo off
cd /d "K:\Fluxgroup\FluxGroup" || exit /b 1
set PYTHONIOENCODING=utf-8
python Tools\fleet\workgen.py --root "K:\Fluxgroup\FluxGroup" --node bm-c >> cph4\fleet\plans\workgen_task.log 2>&1
exit /b 0
