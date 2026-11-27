@echo off
REM HQ-ProductionClaim (bm-b) - 5-minute production claim loop.
REM Order: OB-20261027-182254-574 (CEO-PROXY 2026-10-27 18:22) - bm-b had no claim task,
REM so dispatcher POOL cards 0018/0019 sat RE-OFFERED for 8 days.
REM Why a wrapper: task-register.ps1 needs a script file; this pins cwd + utf-8 + log
REM so the claim receipt face is inspectable without opening a console (U060 zero-window).
REM
REM 2026-11-07 (CEO-PROXY event round): this wrapper only ran --pool, and --pool emits a
REM claim INTENT with no execute leg (queue_claim.py header says so). So every real
REM PRODUCTION-QUEUE job pinned to bm-b was unclaimable here - the words drain and the
REM clock resync would never start. Lane mode first (--node), then the pool intents.
cd /d "C:\Fluxgroup\FluxGroup"
set PYTHONIOENCODING=utf-8
"C:\Program Files\Python311\python.exe" Tools\queue_claim.py --node bm-b >> "C:\Fluxgroup\FluxGroup\cph4\fleet\queue-receipts\_claim_task.log" 2>&1
"C:\Program Files\Python311\python.exe" Tools\queue_claim.py --pool --node bm-b >> "C:\Fluxgroup\FluxGroup\cph4\fleet\queue-receipts\_claim_task.log" 2>&1
exit /b %ERRORLEVEL%