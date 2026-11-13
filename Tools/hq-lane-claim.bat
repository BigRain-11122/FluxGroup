@echo off
rem bm-c lane claim leg (rewritten 2026-10-31: the generated version had every line
rem split in two, so cmd failed on the first `cd` and nothing ever claimed).
cd /d "K:\Fluxgroup\FluxGroup" || exit /b 1
set PYTHONIOENCODING=utf-8
set LOG=cph4\fleet\queue-receipts\_lane_task.log
if not exist cph4\fleet\queue-receipts mkdir cph4\fleet\queue-receipts
rem 2026-11-13：v3 自驱接在任务最前面。原因——传家宝代码已同步到 origin，
rem 但 HQ-StationDrive 任务不存在（no-task），常驻自驱装不上；而本任务（HQ-ProductionClaim）
rem 在白名单里可被远程唤醒，所以每次唤醒先跑一轮 v3 自驱（建卡/执行/判据/回执/交接），
rem 再走旧链路收尾。让"能唤醒的任务"把闭环带起来。
set V3LOG=cph4\fleet\rt\visual\log\boot.log
if not exist cph4\fleet\rt\visual\log mkdir cph4\fleet\rt\visual\log
echo [%DATE% %TIME%] v3 station_drive start >> "%V3LOG%"
python Tools\fleet\station_drive.py --station visual --once --run-limit 2 >> "%V3LOG%" 2>&1
echo [%DATE% %TIME%] v3 station_drive end rc=%ERRORLEVEL% >> "%V3LOG%"

echo [%DATE% %TIME%] claim round start >> "%LOG%"
python Tools\fleet\fleet_hb.py --node bm-c --root "%CD%" >> "%LOG%" 2>&1
python Tools\queue_claim.py --node bm-c >> "%LOG%" 2>&1
python Tools\queue_claim.py --pool --node bm-c >> "%LOG%" 2>&1
python Tools\fleet\lane_agent.py --node bm-c --root "%CD%" --max-seconds 600 >> "%LOG%" 2>&1
echo [%DATE% %TIME%] claim round end rc=%ERRORLEVEL% >> "%LOG%"
exit /b %ERRORLEVEL%