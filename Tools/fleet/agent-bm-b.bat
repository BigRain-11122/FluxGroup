@echo off
rem agent-bm-b.bat - bm-b agent launcher (single-tick mode).
rem 2026-11-05 deep-retro fix: the old resident mode (--loop 60 --pull-every 3) never
rem hot-reloads code, so every fleet_lane/agent patch stayed dormant until someone
rem killed the process by hand - the python3->macos infer fix shipped 2 minutes
rem after the resident started and the box then burned rc=9009 on Mac cards for a
rem full day (DOCS-_已封存_盛永康旧软著, 2026-11-05).
rem New mode: the scheduled task fires this bat every 1m; each tick is a fresh
rem process = fresh code. Task MultipleInstances=IgnoreNew prevents overlap while
rem a long card runs inside a tick. Single-flight on heavy GPU cards stays in
rem vb_train_card (pid-checked lock).
cd /d C:\Fluxgroup\FleetAgent
if not exist "Tools\fleet\agent.py" (
  echo AGENT-MISSING Tools\fleet\agent.py not found in C:\Fluxgroup\FleetAgent 1>&2
  exit /b 4
)
if not exist ".codely-cli" mkdir ".codely-cli"
python Tools\fleet\agent.py --node bm-b --push >> .codely-cli\agent-bm-b.log 2>&1
exit /b %ERRORLEVEL%
