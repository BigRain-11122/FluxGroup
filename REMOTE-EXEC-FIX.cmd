@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"
set NODE=%1
if "%NODE%"=="" (
  set NODE=unknown
  echo %CD% | findstr /I /C:"C:\Fluxgroup" >nul 2>&1
  if not errorlevel 1 set NODE=bm-b
  if "!NODE!"=="unknown" (
    echo %CD% | findstr /I /C:"Desktop" >nul 2>&1
    if not errorlevel 1 set NODE=bm-a
  )
)
set ACK=cph4\fleet\cmd\OB-20261103-1230-REMOTE-EXEC-REPAIR.%NODE%.ack.json
set LOG=cph4\fleet\queue-receipts\remote-exec-check-%NODE%.log
if not exist cph4\fleet\queue-receipts mkdir cph4\fleet\queue-receipts

echo ================================================
echo  Remote executor self-check  node=%NODE%
if "!NODE!"=="unknown" echo  WARNING: node not detected - ack will be .unknown.ack.json
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
set PYCMD=python
where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if not errorlevel 1 (
    set PYCMD=py -3
    echo      python not on PATH - falling back to py -3
  ) else (
    echo      NO python and NO py launcher on PATH - install Python first
  )
)
where python >>"%LOG%" 2>&1
where python3 >>"%LOG%" 2>&1
where python
%PYCMD% --version >>"%LOG%" 2>&1
%PYCMD% --version

echo.
echo [3/7] probe python -c
%PYCMD% -c "print('probe-ok')" >>"%LOG%" 2>&1
echo      rc=!errorlevel!

echo.
echo [4/7] probe target script exists
if exist "Tools\fleet\quality_gate.py" (echo      quality_gate.py FOUND) else (echo      quality_gate.py MISSING)

echo.
echo [5/7] run the card that keeps failing (expect rc=0)
%PYCMD% Tools\fleet\quality_gate.py --line bigstream-drama --out cph4\fleet\queue-receipts\quality-bigstream-drama-probe-%NODE%.json >>"%LOG%" 2>&1
set QRC=!errorlevel!
echo      rc=!QRC!
%PYCMD% Tools\fleet\quality_gate.py --line bigstream-drama >>"%LOG%" 2>&1

echo.
echo [6/7] restart executor (lane_agent, detached)
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I python >nul 2>&1
start "" /MIN cmd /c "%PYCMD% Tools\fleet\lane_agent.py --node %NODE% --root . >> cph4\fleet\queue-receipts\lane-%NODE%.log 2>&1"
echo      started: %PYCMD% Tools/fleet/lane_agent.py --node %NODE%

echo.
echo [7/7] write ack
%PYCMD% Tools\fleet\ack_write.py --id OB-20261103-1230-REMOTE-EXEC-REPAIR --node %NODE% --rc !QRC! --log "%LOG%" --root .
echo.
if "!QRC!"=="0" (echo RESULT: HEALTHY - executor works, ack written) else (echo RESULT: STILL BROKEN - send me the log file)
echo.
echo Log: %LOG%
echo Ack: %ACK%
pause