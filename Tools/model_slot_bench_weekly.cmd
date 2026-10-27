# Weekly model-slot re-bench (silent chain entry). CEO 2026-10-27: 迭代更新，不要只理规则。
@echo off
set PY=C:\Program Files\Python311\python.exe
if not exist "%PY%" set PY=python
"%PY%" "C:\Fluxgroup\FluxGroup\Tools\model_slot_bench.py" --weekly
exit /b %ERRORLEVEL%