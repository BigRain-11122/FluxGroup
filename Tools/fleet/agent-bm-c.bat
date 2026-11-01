@echo off
rem The ONE resident executor for bm-c (master design: one agent, one chain).
rem Evidence: every tick is appended to media/logs/agent-bm-c.log - an executor with no
rem trail is exactly the failure class the 10-31 review called out.
cd /d K:\Fluxgroup\FluxGroup
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
if not exist media\logs mkdir media\logs
python Tools\fleet\agent.py --node bm-c --loop 60 >> media\logs\agent-bm-c.log 2>&1