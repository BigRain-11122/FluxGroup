@echo off
rem bm-c 渲染自愈：ComfyUI 假死重启 + 批中断续烧（见 Tools\fleet\comfy_guard.py 头注）
cd /d K:\Fluxgroup\FluxGroup
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
if not exist media\logs mkdir media\logs
python Tools\fleet\comfy_guard.py >> media\logs\comfy-guard.out.txt 2>&1