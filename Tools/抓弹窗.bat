@echo off
chcp 65001 >nul
echo 正在抓弹窗凶手，请让弹窗自然出现，30 秒后自动结束...
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0polish-hunt-popup.ps1"
pause
