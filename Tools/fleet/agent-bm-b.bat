@echo off
rem agent-bm-b.bat - bm-b resident agent launcher.
rem 2026-11-03 root fix: this launcher was missing from origin while the HQ-Agent
rem scheduled task pointed at it, so bm-b's lane leg died rc=1 every minute and the
rem box only looked alive via its heartbeat. Task -> InvisibleRunner.vbs -> this bat
rem -> agent.py (pull -> hb -> claim -> run -> report), one process, one chain.
cd /d C:\Fluxgroup\FleetAgent
if not exist "Tools\fleet\agent.py" (
  echo AGENT-MISSING Tools\fleet\agent.py not found in C:\Fluxgroup\FleetAgent 1>&2
  exit /b 4
)
if not exist ".codely-cli" mkdir ".codely-cli"
python Tools\fleet\agent.py --node bm-b --loop 60 --pull-every 3 --push >> .codely-cli\agent-bm-b.log 2>&1
exit /b %ERRORLEVEL%