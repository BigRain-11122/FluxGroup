# Daily workflow audit (silent chain entry). CEO order 2026-10-27: 每天一次。
@echo off
set PY=C:\Program Files\Python311\python.exe
if not exist "%PY%" set PY=python
"%PY%" "C:\Fluxgroup\FluxGroup\Tools\workflow_audit_daily.py"
exit /b %ERRORLEVEL%