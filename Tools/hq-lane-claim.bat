@echo off
rem bm-c lane claim leg (rewritten 2026-10-31: the generated version had every line
rem split in two, so cmd failed on the first `cd` and nothing ever claimed).
cd /d "K:\Fluxgroup\FluxGroup" || exit /b 1
set PYTHONIOENCODING=utf-8
set LOG=cph4\fleet\queue-receipts\_lane_task.log
if not exist cph4\fleet\queue-receipts mkdir cph4\fleet\queue-receipts
echo [%DATE% %TIME%] claim round start >> "%LOG%"
python Tools\fleet\fleet_hb.py --node bm-c --root "%CD%" >> "%LOG%" 2>&1
python Tools\queue_claim.py --node bm-c >> "%LOG%" 2>&1
python Tools\queue_claim.py --pool --node bm-c >> "%LOG%" 2>&1
python Tools\fleet\lane_agent.py --node bm-c --root "%CD%" --max-seconds 600 >> "%LOG%" 2>&1
echo [%DATE% %TIME%] claim round end rc=%ERRORLEVEL% >> "%LOG%"
exit /b %ERRORLEVEL%