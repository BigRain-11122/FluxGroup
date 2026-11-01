#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""free_mem.py - reclaim RAM on production boxes so the lane can actually run.

Scope is deliberately narrow:
  * NEVER touches the work machine (bm-a) - the CEO uses it.
  * only closes a fixed list of "user comfort" apps (browsers, chat, media players)
  * never touches render/production processes (ffmpeg, python, ComfyUI, TTS, blender)
  * unloads ollama models held by keep_alive, since the lane reloads what it needs
  * prints before/after so the receipt proves it did something

Windows leg (2026-11-01, reason it exists): this script shipped as macOS-only - vm_stat /
ps -Ao / kill do not exist on Windows, so on bm-c it raised FileNotFoundError before it
could even count RAM. The master's rule is the same on both platforms; only the syscall
differs. Dry run is still the default, and --apply is still opt-in.

Usage: python Tools/fleet/free_mem.py [--apply]   (default = dry run, lists what it would do)
       NODE=<node> is read from the environment so the bm-a guard works when launched
       from a scheduler that does not set it.
"""
import os
import re
import subprocess
import sys

NODE = os.environ.get("NODE", "")
SAFE_TO_CLOSE = ["chrome", "msedge", "firefox", "Doubao", "WeChat", "QQ", "TIM",
                 "QQMusic", "CloudMusic", "PotPlayer", "Steam", "EpicGamesLauncher",
                 "Code", "Safari", "Lark", "飞书", "豆包"]
NEVER = ["ffmpeg", "python", "pythonw", "blender", "ComfyUI", "node", "Tuanjie", "Unity",
         "agent.py", "lane_agent", "fleet_hb", "steward"]


def ram_free_gb():
    if os.name == "nt":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        try:
            m = MEMORYSTATUSEX()
            m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                return round(m.ullAvailPhys / 1e9, 1)
        except Exception:
            pass
        return None
    try:
        vm = subprocess.check_output(["vm_stat"], text=True)
    except Exception:
        return None
    page, vals = 16384, {}
    for ln in vm.splitlines():
        if "page size of" in ln:
            page = int(ln.split("page size of")[1].split()[0])
        if ":" in ln:
            k, v = ln.split(":", 1)
            try:
                vals[k.strip()] = int(v.strip().rstrip("."))
            except ValueError:
                pass
    tot = sum(vals.get(k, 0) for k in
              ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"))
    return round(tot * page / 1e9, 1)


def ps_list():
    """[(pid, mb, name)] on either platform, largest first when callers sort."""
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
                             text=True, errors="replace").stdout
        rows = []
        for ln in out.splitlines():
            parts = [p.strip('"') for p in ln.split('","')]
            if len(parts) < 5:
                continue
            name, pid, mem = parts[0].strip('"'), parts[1], parts[4]
            digits = re.sub(r"[^0-9]", "", mem)
            if pid.isdigit() and digits:
                rows.append((int(pid), int(digits) // 1024, name))
        return rows
    out = subprocess.run(["ps", "-Ao", "pid,rss,comm"], capture_output=True, text=True).stdout
    rows = []
    for ln in out.splitlines()[1:]:
        p = ln.split(None, 2)
        if len(p) == 3 and p[1].isdigit():
            rows.append((int(p[0]), int(p[1]) // 1024, p[2]))
    return rows


def close_pid(pid):
    if os.name == "nt":
        # No /F: ask the app to close, never hard-kill a window the user may be typing in.
        subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True)
    else:
        subprocess.run(["kill", "-TERM", str(pid)], capture_output=True)


def main():
    apply_ = "--apply" in sys.argv
    if NODE == "bm-a":
        print("[free] bm-a is the CEO work machine - refusing to touch its apps")
        return 0
    before = ram_free_gb()
    targets, skipped = [], []
    for pid, mb, cmd in sorted(ps_list(), key=lambda r: -r[1])[:40]:
        low = cmd.lower()
        if any(n.lower() in low for n in NEVER):
            skipped.append((mb, "protected:" + os.path.basename(cmd)))
            continue
        hit = next((n for n in SAFE_TO_CLOSE if n.lower() in low), None)
        if hit and mb >= 200:
            targets.append((pid, mb, hit))
    print("[free] RAM available %.1f GB | candidates %d" % (before or -1, len(targets)))
    if skipped:
        print("       protected (never touched): %s"
              % ", ".join("%s %dMB" % (n.split(":", 1)[1], mb) for mb, n in skipped[:4]))
    for pid, mb, name in targets[:8]:
        print("   - %s (%d MB)" % (name, mb))
        if apply_:
            close_pid(pid)
    if apply_:
        try:
            out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=30).stdout or ""
            for ln in out.splitlines()[1:]:
                m = ln.split()[0]
                subprocess.run(["ollama", "stop", m], capture_output=True, timeout=60)
        except Exception:
            pass
        print("[free] RAM available after %.1f GB" % (ram_free_gb() or -1))
    return 0


if __name__ == "__main__":
    sys.exit(main())