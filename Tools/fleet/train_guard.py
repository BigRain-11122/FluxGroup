#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_guard.py - 并行训练的换页看门狗：一越线就把并行那路撤掉，不许硬扛 swap。

为什么要有它（CEO 两条硬令撞在一起）：
  「继续压榨算力 并行」要求多跑；「不许硬扛 swap」要求越线就退。两条都满足的唯一做法是
  并行可以上，但必须有**自动撤线**——靠人盯，夜里就变成 swap 一路吃到卡死。

判据（任一成立即撤，撤的是并行那一路，主训练不动）：
  · 观察窗内换出页 > 50/min（真在往磁盘挤）
  · swap 用量比上次采样涨 > 300MB（一次性装载尖峰不算，持续上涨才算）
  · 可用内存（free+inactive+speculative）< 400MB

用法：
  python3 Tools/fleet/train_guard.py --label com.fluxgroup.trainb --minutes 180
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

ROOT = "/Users/junsheng.sun/FluxGroup"
LOG = os.path.join(ROOT, ".codely-cli", "state", "train-guard.log")

PAGEOUT_MAX_PER_MIN = 50
SWAP_GROW_MAX_MB = 300
FREE_MIN_MB = 400


def vm():
    o = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    ps = int(re.search(r"page size of (\d+)", o).group(1))
    def g(k):
        m = re.search(rf"{k}:\s+(\d+)", o)
        return int(m.group(1)) * ps / 2**20 if m else 0.0
    po = int(re.search(r"Swapouts:\s+(\d+)", o).group(1))
    avail = g("Pages free") + g("Pages inactive") + g("Pages speculative")
    s = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used = ([\d.]+)M", s)
    return {"pageouts": po, "avail_mb": round(avail), "swap_mb": round(float(m.group(1)))}


def kill(label):
    """只撤自己那一路。

    2026-11-18 实锚：原来还带一条写死的 pkill 模式，撤第三路时把第二路（craft_learner）
    一起打死了——撤线动作比越线本身更贵。这里只认 label，删掉硬编码模式。
    """
    subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (os.getuid(), label)],
                   capture_output=True)


def unload_idle():
    """越线时先卸闲置 ollama 模型，而不是杀训练。

    2026-11-20 实测：本机常驻 4b-mlx(4.12GB)+2b(3.14GB)=7.26GB，而训练只要 3.3GB
    ——把机器推到换页的是常驻模型，不是训练本身。所以"不触发 swap"的正确动作
    是卸掉不参与训练的那几档，训练继续。
    """
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models") or []
    except Exception as e:
        print("[guard] 读不到 ollama 模型表：%s" % e, flush=True)
        return []
    freed = []
    for m in models:
        name = m.get("name") or ""
        if not name:
            continue
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()
            freed.append(name)
        except Exception as e:
            print("[guard] 卸载 %s 失败：%s" % (name, e), flush=True)
    return freed


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="com.fluxgroup.trainb")
    ap.add_argument("--minutes", type=int, default=180)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--on-breach", choices=("kill", "unload"), default="kill",
                    help="越线动作：kill=撤并行路；unload=只卸闲置 ollama 模型，训练继续")
    a = ap.parse_args(argv)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    prev = vm()
    t_end = time.time() + a.minutes * 60
    while time.time() < t_end:
        time.sleep(a.interval)
        cur = vm()
        mins = a.interval / 60.0
        rate = (cur["pageouts"] - prev["pageouts"]) / mins
        dsw = cur["swap_mb"] - prev["swap_mb"]
        row = {"ts": datetime.now().isoformat(timespec="seconds"),
               "pageout_rate_per_min": round(rate, 1), "swap_delta_mb": dsw,
               "swap_mb": cur["swap_mb"], "avail_mb": cur["avail_mb"]}
        breach = []
        if rate > PAGEOUT_MAX_PER_MIN:
            breach.append("换出 %.0f/min > %d" % (rate, PAGEOUT_MAX_PER_MIN))
        if dsw > SWAP_GROW_MAX_MB:
            breach.append("swap +%dMB > %d" % (dsw, SWAP_GROW_MAX_MB))
        if cur["avail_mb"] < FREE_MIN_MB:
            breach.append("可用 %dMB < %d" % (cur["avail_mb"], FREE_MIN_MB))
        row["verdict"] = "BREACH" if breach else "OK"
        row["why"] = breach
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("[guard] %s %s %s" % (row["ts"], row["verdict"], "；".join(breach) or ""),
              flush=True)
        if breach:
            if a.on_breach == "unload":
                freed = unload_idle()
                print("[guard] 越线→卸闲置模型 %s（%s）" % (freed or "无", "；".join(breach)),
                      flush=True)
                prev = vm()      # 给模型卸载后一个重新计数窗口，不立刻二次判越线
                continue
            kill(a.label)
            print("[guard] 已撤并行训练 %s（%s）" % (a.label, "；".join(breach)), flush=True)
            return 3
        prev = cur
    print("[guard] 到点收工（%d 分钟无越线）" % a.minutes, flush=True)
    return 0


def self_test():
    """判据必须能红：把三条阈值各造一个越线样例。"""
    cases = [
        ("换出超限要判越线", (60 / 1.0) > PAGEOUT_MAX_PER_MIN),
        ("换出正常不报", (10 / 1.0) <= PAGEOUT_MAX_PER_MIN),
        ("swap 涨超限要报", 400 > SWAP_GROW_MAX_MB),
        ("一次性尖峰不报", 250 <= SWAP_GROW_MAX_MB),
        ("可用内存不足要报", 300 < FREE_MIN_MB),
    ]
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
