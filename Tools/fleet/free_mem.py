#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""free_mem.py - reclaim RAM on production boxes so the lane can actually run.

Scope is deliberately narrow:
  * NEVER touches the work machine (bm-a) - the CEO uses it.
  * only closes a fixed list of "user comfort" apps (browsers, chat, media players)
  * never touches render/production processes (ffmpeg, python, ComfyUI, TTS, blender)
  * unloads ollama models held by keep_alive, since the lane reloads what it needs
  * prints before/after so the receipt proves it did something

Usage: python Tools/fleet/free_mem.py [--apply]   (default = dry run, lists what it would do)
"""
import os, re, subprocess, sys

NODE = os.environ.get("NODE", "")
SAFE_TO_CLOSE = ["chrome", "msedge", "firefox", "Doubao", "WeChat", "QQ", "TIM",
                 "QQMusic", "CloudMusic", "PotPlayer", "Steam", "EpicGamesLauncher",
                 "Code", "Safari", "Lark", "飞书", "豆包"]
NEVER = ["ffmpeg", "python", "pythonw", "blender", "ComfyUI", "node", "Tuanjie", "Unity",
         "agent.py", "lane_agent", "fleet_hb", "steward"]


def ram_free_gb():
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
    out = subprocess.run(["ps", "-Ao", "pid,rss,comm"], capture_output=True, text=True).stdout
    rows = []
    for ln in out.splitlines()[1:]:
        p = ln.split(None, 2)
        if len(p) == 3 and p[1].isdigit():
            rows.append((int(p[0]), int(p[1]) // 1024, p[2]))
    return rows


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
    for pid, mb, name in targets[:8]:
        print("   - %s (%d MB)" % (name, mb))
        if apply_:
            subprocess.run(["kill", "-TERM", str(pid)], capture_output=True)
    if apply_:
        subprocess.run(["ollama", "ps"], capture_output=True)
        for ln in (subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout or "").splitlines()[1:]:
            m = ln.split()[0]
            subprocess.run(["ollama", "stop", m], capture_output=True)
        print("[free] RAM available after %.1f GB" % (ram_free_gb() or -1))
    return 0


if __name__ == "__main__":
    sys.exit(main())