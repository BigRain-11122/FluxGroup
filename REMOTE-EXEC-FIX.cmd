@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"
set NODE=%1
if "%NODE%"=="" set NODE=unknown
set ACK=cph4\fleet\cmd\OB-20261103-1230-REMOTE-EXEC-REPAIR.%NODE%.ack.json
set LOG=cph4\fleet\queue-receipts\remote-exec-check-%NODE%.log
if not exist cph4\fleet\queue-receipts mkdir cph4\fleet\queue-receipts

echo ================================================
echo  Remote executor self-check  node=%NODE%
echo  repo=%CD%
echo ================================================
echo.

echo [1/7] git pull
git pull --ff-only --no-rebase origin main >>"%LOG%" 2>&1
set PULLRC=!errorlevel!
echo      rc=!PULLRC!
if not "!PULLRC!"=="0" (
  echo      pull failed - show status
  git status --porcelain >>"%LOG%" 2>&1
  git status --porcelain
)

echo.
echo [2/7] python interpreter
where python >>"%LOG%" 2>&1
where python3 >>"%LOG%" 2>&1
where python
python --version >>"%LOG%" 2>&1
python --version

echo.
echo [3/7] probe python -c
python -c "print('probe-ok')" >>"%LOG%" 2>&1
echo      rc=!errorlevel!

echo.
echo [4/7] probe target script exists
if exist "Tools\fleet\quality_gate.py" (echo      quality_gate.py FOUND) else (echo      quality_gate.py MISSING)

echo.
echo [5/7] run the card that keeps failing (expect rc=0)
python Tools\fleet\quality_gate.py --line bigstream-drama --out cph4\fleet\queue-receipts\quality-bigstream-drama-probe-%NODE%.json >>"%LOG%" 2>&1
set QRC=!errorlevel!
echo      rc=!QRC!
python Tools\fleet\quality_gate.py --line bigstream-drama >>"%LOG%" 2>&1

echo.
echo [6/7] restart executor (lane_agent, detached)
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I python >nul 2>&1
start "" /MIN cmd /c "python Tools\fleet\lane_agent.py --node %NODE% --root . >> cph4\fleet\queue-receipts\lane-%NODE%.log 2>&1"
echo      started: python Tools/fleet/lane_agent.py --node %NODE%

echo.
echo [7/7] write ack
python Tools\fleet\ack_write.py --id OB-20261103-1230-REMOTE-EXEC-REPAIR --node %NODE% --rc !QRC! --log "%LOG%" --root .
echo.
echo.
if "!QRC!"=="0" (echo RESULT: HEALTHY - executor works, ack written) else (echo RESULT: STILL BROKEN - send me the log file)
echo.
echo Log: %LOG%
echo Ack: %ACK%
pause