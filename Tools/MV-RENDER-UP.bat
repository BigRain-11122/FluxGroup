@echo off
REM MV-RENDER-UP - double-click this on the GPU box to start the MV renderer (ComfyUI) for the fleet.
REM It starts ComfyUI listening on 0.0.0.0:8188 so the HQ box can submit MV jobs over the tailnet.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mv-render-up.ps1" %*
echo.
echo ---- status file: %USERPROFILE%\.codely-cli\mv-render-status.json
pause