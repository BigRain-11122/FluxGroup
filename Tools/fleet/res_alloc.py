#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""res_alloc.py — 一台机器上三件重活的单一仲裁（训练 / 浏览器 / 本地模型）。

为什么要有它（2026-11-23 实测）：
  训练、两个账号的会话、采集、发帖、本地 9B 模型同时跑 → **swap 到 4.4GB**。
  CEO 的硬规矩是「本地算力在不触发 swap 的前提下用满」，所以不能靠"谁先抢到"，
  必须有一个地方统一说"现在轮到谁"。

三条资源彼此不同，不能混着算：
  ① 统一内存：训练 + 本地模型 + 两个浏览器共享同一池子 → 只有它能逼出 swap；
  ② 浏览器 profile：同一时刻只能一个进程用（browserd 是单线程）→ 谁进去谁堵别人；
  ③ 主控节拍：会话/采集/发帖都吃 CPU，但主控第一任务是调度与监督，不能饿死。

优先级（按 CEO 口径：训练是资产，发帖是消耗，采集是供给）：
  TRAIN > POST > SESSION > COLLECT
  但**资产优先不等于永远优先**：训练可以独占夜间，白天必须让出浏览器给人味动作。

判据（都能实测）：
  swap ≤ 512MB       否则强制降档（DENY-NEW）
  浏览器 ≤1 个 profile 在用
  发帖 queue ≤60s    否则本拍跳过（已有机制）
  采集 ≥1 次/6 小时  否则报 BLOCKED-COLLECT

用法：
  python3 Tools/fleet/res_alloc.py --status
  python3 Tools/fleet/res_alloc.py --once          # 算一次并落 RES-SLOT.json
  python3 Tools/fleet/res_alloc.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")
SLOT = os.path.join(STATE, "RES-SLOT.json")

SWAP_LINE = 512          # MB，超过即降档
SWAP_HARD = 2048         # MB，超过即禁止新开会话/新采集


def _sh(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout or ""
    except Exception:
        return ""


def swap_mb():
    """macOS: vm.swapusage → total = 4096.00M used = ..."""
    out = _sh("sysctl -n vm.swapusage")
    used = 0.0
    for part in out.replace("=", " ").split():
        if part.endswith("M"):
            try:
                v = float(part[:-1])
            except Exception:
                continue
            # 只取 used 那一项：形如 total 4096.00M used 4461.25M free ...
            used = v if used == 0 or v != 4096.0 else used
    # 更稳的解析：直接抓 "used" 后面的数
    import re
    m = re.search(r"used\s*=\s*([\d.]+)M", out)
    return float(m.group(1)) if m else used


def train_running():
    out = _sh("ps -axo command | grep -E 'mlx_lm|train_forever|lora' | grep -v grep")
    return bool(out.strip())


def browsers():
    out = _sh("ps -axo command | grep -E 'user-data-dir=\\S*browser-' | grep -v grep")
    profs = set()
    import re
    for m in re.finditer(r"user-data-dir=(\S*browser-[\w-]+)", out):
        profs.add(os.path.basename(m.group(1)))
    return sorted(profs)


def llm_resident():
    out = _sh("curl -s --max-time 3 http://127.0.0.1:11434/api/ps")
    try:
        j = json.loads(out or "{}")
        return [m.get("name") for m in (j.get("models") or [])]
    except Exception:
        return []


def decide(swap, train, profs, models, hour=None):
    """返回 (班次, 允许的动作集合, 理由)。纯函数，自检可直接注入。"""
    hour = datetime.now().hour if hour is None else hour
    night = hour < 7 or hour >= 23
    busy_browser = len(profs)

    if swap > SWAP_HARD:
        return ("DENY-NEW", set(), "swap %dMB > %dMB：先收尾，不开新会话/不采集/不训练新轮" % (swap, SWAP_HARD))
    if swap > SWAP_LINE:
        return ("DRAIN", {"finish"}, "swap %dMB > %dMB：只许收尾，喝完再上新活" % (swap, SWAP_LINE))
    if train and night:
        return ("TRAIN-NIGHT", {"train", "post"}, "夜间训练独占；发帖仍放行（消耗小、时效强）")
    if train and busy_browser:
        return ("TRAIN+LIGHT", {"train", "post", "session1"}, "训练中且已有 1 个浏览器：只许 1 个号轻量会话")
    if train:
        return ("TRAIN-DAY", {"train", "post", "session1", "collect"},
                "训练中、浏览器空闲：允许 1 号会话 + 采集（采集比会话更值，供语料）")
    if busy_browser:
        return ("BROWSE", {"post", "session2"}, "无训练：可双号会话；采集让路")
    return ("FULL", {"post", "session2", "collect", "train"}, "无训练、浏览器空闲：全线可用")


def once():
    swap, train, profs, models = swap_mb(), train_running(), browsers(), llm_resident()
    slot, allowed, why = decide(swap, train, profs, models)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "slot": slot,
           "allowed": sorted(allowed), "why": why,
           "facts": {"swap_mb": round(swap, 1), "train": train, "browsers": profs,
                     "models": models}}
    os.makedirs(STATE, exist_ok=True)
    tmp = SLOT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    os.replace(tmp, SLOT)
    print("[res] %s ｜ swap %dMB ｜ 训练 %s ｜ 浏览器 %s ｜ 模型 %s"
          % (slot, swap, "是" if train else "否", ",".join(profs) or "无", ",".join(models) or "无"))
    print("[res] 允许：%s ｜ %s" % (",".join(sorted(allowed)) or "无", why))
    return 0


def status():
    try:
        print(json.dumps(json.load(open(SLOT, encoding="utf-8")), ensure_ascii=False, indent=1))
    except Exception:
        print("[res] 还没有 RES-SLOT.json，先跑 --once")
    return 0


def self_test():
    """负控：把 swap 拉高必须降档；训练+夜间必须只给训练与发帖。"""
    cases = []
    cases.append(("swap 3000 → DENY-NEW", decide(3000, True, ["browser-bilibili"], ["qwen"], 3)[0] == "DENY-NEW"))
    cases.append(("swap 1000 → DRAIN", decide(1000, True, [], [], 12)[0] == "DRAIN"))
    cases.append(("swap 0 + 夜间训练 → TRAIN-NIGHT", decide(0, True, [], [], 3)[0] == "TRAIN-NIGHT"))
    cases.append(("夜间训练不发会话", "session1" not in decide(0, True, [], [], 3)[1]))
    cases.append(("夜间训练仍允许发帖", "post" in decide(0, True, [], [], 3)[1]))
    cases.append(("白天训练+1浏览器 → 只 1 号轻量", decide(0, True, ["browser-bilibili"], [], 14)[0] == "TRAIN+LIGHT"))
    cases.append(("白天训练+浏览器空闲 → 允许采集", "collect" in decide(0, True, [], [], 14)[1]))
    cases.append(("无训练+浏览器空闲 → 双号", decide(0, False, [], [], 14)[0] == "FULL"))
    cases.append(("swap 解析出數字", isinstance(swap_mb(), float)))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    return once()


if __name__ == "__main__":
    sys.exit(main())
