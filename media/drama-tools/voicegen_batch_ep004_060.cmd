# Batch voicegen EP004-EP060 (S4U, silent chain). Valve-gated GPU lane.
@echo off
set PY=C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts\.venv\Scripts\python.exe
set SCRIPT=C:\Fluxgroup\FluxGroup\media\drama-tools\drama_voicegen_batch.py
cd /d C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts
"%PY%" "%SCRIPT%" EP004-EP060 --out-name r1200_ep004_060
exit /b %ERRORLEVEL%