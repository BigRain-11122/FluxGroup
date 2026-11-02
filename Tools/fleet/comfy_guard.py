#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comfy_guard.py - keep the render service and the current batch alive on bm-c.

Why (measured 2026-11-01, three wedges in one evening):
  H3 i2v stages ~19.995GB of weights (UNET int8 + LoRA + qwen3vl-32b CLIP) through system
  RAM into a 16GB card. While a 14s shot renders, free RAM falls to ~2GB; when it runs out
  ComfyUI dies in one of two ways:
    (a) process gone,            (b) process alive but 8188 no longer listening.
  Both look identical to the runner: it just keeps printing "N s running..." until its own
  900s timeout, and the batch silently stalls with zero output. Nothing on the box noticed,
  which is why the GPU sat at 0% for hours with a "healthy" process list.

What this does, every run (intended cadence: 3 minutes):
  1. if 8188 is not serving -> start ComfyUI hidden and wait for /system_stats
  2. if a batch is declared (flag file) and no runner process matches it -> relaunch it
     (the runner skips finished clips, so a relaunch resumes instead of redoing work)
  3. never touch anything while the CEO's yield flag is set

Flag file: cph4/fleet/mv-album-001-jay/local-i2v/BURN-ZONE.json
  {"name": "...", "cmd": ["python", "..."], "log": "media/.../log.txt", "match": "h3_i2v_album"}
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
COMFY = r"D:\ComfyUI\python_embeded\python.exe"
COMFY_MAIN = r"D:\ComfyUI\ComfyUI\main.py"
COMFY_CWD = r"D:\ComfyUI\ComfyUI"
PORT = 8188
FLAG = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "local-i2v", "BURN-ZONE.json")
PAUSE = os.path.join(ROOT, ".codely-cli", "machine-state.flag")
LOGDIR = os.path.join(ROOT, "media", "logs")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def log(msg):
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(os.path.join(LOGDIR, "comfy-guard.log"), "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg))
    except Exception:
        pass


def serving(timeout=3):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/system_stats" % PORT, timeout=timeout):
            return True
    except Exception:
        return False


def comfy_pids():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*ComfyUI*main.py*' }).ProcessId"],
            capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW).stdout
        return [int(x) for x in out.split() if x.strip().isdigit()]
    except Exception:
        return []


def start_comfy(wait_s=240):
    try:
        subprocess.Popen([COMFY, "-s", COMFY_MAIN, "--listen", "127.0.0.1", "--port", str(PORT)],
                         cwd=COMFY_CWD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=NO_WINDOW)
    except Exception as e:
        log("start failed: %s" % e)
        return False
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if serving():
            log("comfy started and serving")
            return True
        time.sleep(5)
    log("comfy started but never served within %ss" % wait_s)
    return False


def runner_pids(match):
    if not match:
        return []
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*%s*' -and "
             "$_.Name -like 'python*' }).ProcessId" % match],
            capture_output=True, text=True, timeout=60, creationflags=NO_WINDOW).stdout
        return [int(x) for x in out.split() if x.strip().isdigit()]
    except Exception:
        return []


def free_ram_gb():
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return round(m.ullAvailPhys / 1e9, 1)
    except Exception:
        pass
    return None


def reclaim_webview(below_gb=4.0):
    """SearchHost spawns tens of msedgewebview2 children that nobody closes; measured
    36 processes / ~5GB, and they respawn within minutes. Only touched when the render is
    already short of RAM, and only the ones whose ROOT parent is SearchHost - never a
    browser window the CEO is looking at."""
    ram = free_ram_gb()
    if ram is None or ram >= below_gb:
        return 0
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$r=@(); Get-CimInstance Win32_Process -Filter \"Name='msedgewebview2.exe'\" | "
             "ForEach-Object { $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$_.ParentProcessId); "
             "if ($p -and $p.Name -eq 'SearchHost.exe') { $r += $_.ProcessId } }; $r -join ','"],
            capture_output=True, text=True, timeout=90, creationflags=NO_WINDOW).stdout
        pids = [x.strip() for x in out.strip().split(",") if x.strip().isdigit()]
        for pid in pids:
            subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True,
                           timeout=30, creationflags=NO_WINDOW)
        if pids:
            log("reclaimed %d SearchHost webview process(es) at ram=%.1fGB" % (len(pids), ram))
        return len(pids)
    except Exception as e:
        log("webview reclaim failed: %s" % e)
        return 0


def main():
    if "--once" not in sys.argv:
        pass
    if os.path.exists(PAUSE):
        log("pause flag present (CEO yield) - standing down")
        return 0

    if not serving():
        pids = comfy_pids()
        log("8188 down (comfy pids=%s) -> restarting" % (pids or "none"))
        # A wedged process (alive, not listening) must be cleared first or the port stays dead.
        for pid in pids:
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                               capture_output=True, timeout=60, creationflags=NO_WINDOW)
            except Exception:
                pass
        time.sleep(3)
        if not start_comfy():
            return 1

    reclaim_webview()

    if not os.path.exists(FLAG):
        return 0
    try:
        with open(FLAG, encoding="utf-8-sig") as f:
            spec = json.load(f)
    except Exception as e:
        log("flag unreadable: %s" % e)
        return 0
    if spec.get("done"):
        return 0

    match = spec.get("match") or ""
    if runner_pids(match):
        return 0                      # the batch owns the GPU; nothing to do
    cmd = spec.get("cmd") or []
    if not cmd:
        return 0
    logpath = os.path.join(ROOT, spec.get("log", "media/logs/burn.log").replace("/", os.sep))
    os.makedirs(os.path.dirname(logpath), exist_ok=True)
    try:
        with open(logpath, "a", encoding="utf-8") as f:
            f.write("\n[%s] guard relaunch: %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                     " ".join(cmd)))
        fh = open(logpath, "a", encoding="utf-8")
        subprocess.Popen(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                         creationflags=NO_WINDOW)
        log("relaunched batch: %s" % " ".join(cmd)[:120])
    except Exception as e:
        log("relaunch failed: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())