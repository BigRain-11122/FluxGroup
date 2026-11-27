#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comfy_mode.py — 切换本机 ComfyUI 运行模式（单实例纪律）

为什么（2026-11-22 实测）：本机同一时刻必须只有**一个** ComfyUI，而且两种模式互斥——
  · `lowvram`  ：krea2(12.24G) + qwen3vl_4b(4.89G) ≈ 17.1G > 16G，不 lowvram 会整进程消失；
  · `normal`   ：H3 视频模型必须正常模式，lowvram 下会被换入换出拖成假死（实测 7 分钟零帧）。

用法：
  python Tools/comfy_mode.py lowvram      # 重启到低显存模式（krea2 出图用）
  python Tools/comfy_mode.py normal       # 重启到正常模式（H3 i2v 用）
  python Tools/comfy_mode.py status
Exit: 0 已就位；2 起不来
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

COMFY_PY = r"D:\ComfyUI\python_embeded\python.exe"
COMFY_MAIN = r"D:\ComfyUI\ComfyUI\main.py"
COMFY_CWD = r"D:\ComfyUI\ComfyUI"
PORT = 8188
NO_WIN = 0x08000000


def sh(cmd, timeout=40):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              errors="replace", timeout=timeout,
                              creationflags=NO_WIN).stdout.strip()
    except Exception:
        return ""


def pids():
    out = sh('powershell -NoProfile -Command "Get-CimInstance Win32_Process | '
             'Where-Object {$_.CommandLine -like \'*ComfyUI*main.py*\'} | '
             'ForEach-Object { $_.ProcessId } | ConvertTo-Json -Compress"')
    try:
        d = json.loads(out) if out else []
    except Exception:
        d = []
    if isinstance(d, int):
        d = [d]
    return d or []


def mode_of(pid):
    out = sh('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter '
             '\'ProcessId=%d\').CommandLine"' % pid)
    return "lowvram" if "--lowvram" in out else "normal"


def serving():
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/system_stats" % PORT, timeout=6).read()
        return True
    except Exception:
        return False


def kill_all(deadline=25):
    for p in pids():
        sh("taskkill /F /PID %d" % p, timeout=20)
    t0 = time.time()
    while pids() and time.time() - t0 < deadline:
        time.sleep(1)
    return not pids()


def start(mode):
    args = ["-s", COMFY_MAIN, "--listen", "127.0.0.1", "--port", str(PORT)]
    if mode == "lowvram":
        args.append("--lowvram")
    else:
        args.append("--disable-smart-memory")
    subprocess.Popen([COMFY_PY] + args, cwd=COMFY_CWD, creationflags=NO_WIN,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 300:
        if serving():
            return True
        time.sleep(3)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["lowvram", "normal", "status"])
    a = ap.parse_args()

    if a.mode == "status":
        ps = pids()
        print(json.dumps({"pids": ps, "modes": [mode_of(p) for p in ps], "serving": serving()}))
        return 0

    cur = [mode_of(p) for p in pids()]
    if serving() and cur and all(m == a.mode for m in cur) and len(cur) == 1:
        print("already %s (pid=%s)" % (a.mode, cur and pids()))
        return 0
    print("switching to %s (current=%s serving=%s)" % (a.mode, cur, serving()))
    if not kill_all():
        print("WARN: 有进程杀不掉（CUDA 挂死）→ 需重启机器")
        return 2
    if not start(a.mode):
        print("FAIL: %s 起不来" % a.mode)
        return 2
    print("OK %s" % a.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
