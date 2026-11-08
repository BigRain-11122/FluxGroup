@echo off
REM bm-a production claim loop, WITH a log file.
REM Why: the task used to call pythonw.exe directly, so sys.stdout was None and any
REM traceback (or print) died silently - 8.5h of zero output with LastResult=267009
REM (still running) looked identical to "working". python.exe + redirect keeps the
REM evidence on disk; InvisibleRunner.vbs keeps the window invisible.
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d C:\Users\sjs20\Desktop\FluxGroup
"C:\Users\sjs20\AppData\Local\Programs\Python\Python314\python.exe" Tools\queue_claim.py --node bm-a >> "C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\queue-receipts\_claim_bm-a.log" 2>&1
exit /b %ERRORLEVEL%