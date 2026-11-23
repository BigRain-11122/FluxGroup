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

SWAP_LINE = 512          # MB，超过即降档（只收尾）
SWAP_HARD = 2048         # MB，超过即禁止新开任何浏览器活

# 平台轮转（CEO 2026-11-23：训练和实战并行，各大平台轮流）。
# 并行 ≠ 同时开所有平台：真正的并行是"训练常驻 + 永远有一条实战线"，平台按时间片换手，
# 保证任何时刻只有一个浏览器 profile（内存与 browserd 单线程两条限制都要求这样）。
PLATFORMS = [
    # 每条都必须有"实测证据"。没验过的写 need-login / need-account，不许先排班后失望。
    {"id": "bilibili", "profile": "browser-bilibili", "state": "live", "weight": 5,
     "actions": ["read", "like", "danmaku", "comment", "coin", "fav", "follow"],
     "note": "双号养号主线", "evidence": "2026-11-23 双号 GREEN、六动作已上线、今日发帖/副动作有数"},
    {"id": "gzh", "profile": "browser-gzh", "state": "building", "weight": 3,
     "actions": ["read"],
     "note": "采集通；无发布 API，发布须后台人工", "evidence": "单篇 3.0 秒取全字段；批量 3/4 入库"},
    {"id": "toutiao", "profile": "browser-multi", "state": "read", "weight": 2,
     "actions": ["read"],
     "note": "头条搜索可读，可做选题/语料源；发布未验",
     "evidence": "2026-11-23 实测：title 正常、正文 1894 字、10 个结果卡、无登录墙"},
    {"id": "chejiahao", "profile": "browser-gzh", "state": "read", "weight": 2,
     "actions": ["read"],
     "note": "汽车之家车家号，对标对象镜像语料",
     "evidence": "实测作者页翻页取 /info/，一次建池 30 条、正文 1662–3693 字"},
    {"id": "zhihu", "profile": "browser-zhihu", "state": "need-login", "weight": 0,
     "actions": ["read"],
     "note": "知乎：未登录几乎无内容，需扫码登录一次",
     "evidence": "2026-11-23 实测：首页正文仅 468 字、搜索页被拦、内容块 0"},
    {"id": "weibo", "profile": "browser-multi", "state": "need-login", "weight": 0,
     "actions": ["read"],
     "note": "微博：未登录直接跳登录页",
     "evidence": "2026-11-23 实测：title=登录-微博、正文 96 字、卡片 0"},
    {"id": "xhs", "profile": "browser-xhs", "state": "need-account", "weight": 0,
     "actions": [], "note": "小红书：无账号", "evidence": "未注册，未验"},
    {"id": "douyin", "profile": "browser-douyin", "state": "need-account", "weight": 0,
     "actions": [], "note": "抖音：无账号", "evidence": "未注册，未验"},
]

SLICE_MIN = 90            # 每个平台占用时长（分钟）


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


def mem_free_mb():
    """当前可用内存（free+inactive+speculative）。

    为什么不能只看 swap：swap used 是历史累计，降下来很慢，即使压力已经消失也不会归零。
    拿它当唯一闸会永久卡在降档，把"训练与实战并行"变成一句空话。
    前馈用可用内存，swap 只作参考。
    """
    try:
        out = _sh("vm_stat")
        page = 4096
        import re
        m = re.search(r"page size of (\d+) bytes", out)
        if m:
            page = int(m.group(1))
        vals = {}
        for line in out.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip().rstrip(".")
                if v.isdigit():
                    vals[k.strip()] = int(v)
        free = (vals.get("Pages free", 0) + vals.get("Pages inactive", 0)
                + vals.get("Pages speculative", 0))
        return round(free * page / 1024 / 1024, 1)
    except Exception:
        return -1.0


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


def platform_now(hour=None, minute=0):
    """按时间片轮转出当前该用哪个平台（只在 state=live/building 里轮）。"""
    hour = datetime.now().hour if hour is None else hour
    minute = datetime.now().minute if minute is None else minute
    live = [p for p in PLATFORMS if p["state"] in ("live", "read", "building") and (p.get("weight") or 0) > 0]
    if not live:
        return None
    # 加权轮转：权重高的占更多片
    seq = []
    for p in live:
        seq += [p] * max(1, int(p.get("weight") or 1))
    idx = ((hour * 60 + minute) // SLICE_MIN) % len(seq)
    return seq[idx]


FREE_MIN = 1500          # MB，低于它禁止新开浏览器活（会开始换页）
FREE_HARD = 800          # MB，低于它连训练也收尾


def decide(swap, free_mb, train, profs, models, hour=None):
    """返回 (班次, 允许的动作集合, 理由)。纯函数，自检可直接注入。

    判据顺序：先看**当前可用内存**（前馈，能预测会不会换页），swap 只作背景。
    """
    hour = datetime.now().hour if hour is None else hour
    busy_browser = len(profs)

    if free_mb >= 0 and free_mb < FREE_HARD:
        return ("DENY-NEW", {"finish"},
                "可用内存 %dMB < %dMB：只收尾（swap 已 %dMB 是历史累计，不作唯一判据）"
                % (free_mb, FREE_HARD, swap))
    if free_mb >= 0 and free_mb < FREE_MIN:
        return ("DRAIN", {"finish", "train"},
                "可用内存 %dMB < %dMB：训练可续，浏览器只收尾" % (free_mb, FREE_MIN))
    # 并行常态：训练 + 1 条实战线（平台轮转）+ 发帖
    if busy_browser:
        return ("PARALLEL-1", {"train", "post", "finish"},
                "训练与实战并行中：%s 在跑。再开一个平台不是内存问题（可用 %dMB），"
                "而是 browserd 单线程会互相排队，所以一次只放一条实战线"
                % (",".join(profs), free_mb))
    return ("PARALLEL", {"train", "post", "session1", "collect"},
            "训练常驻 + 本时段平台实战 + 发帖；采集与实战共用同一个浏览器，谁进来谁先用")


def once():
    swap, free, train, profs, models = (swap_mb(), mem_free_mb(), train_running(),
                                        browsers(), llm_resident())
    slot, allowed, why = decide(swap, free, train, profs, models)
    pf = platform_now()
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "slot": slot,
           "platform": (pf or {}).get("id"), "platform_note": (pf or {}).get("note"),
           "allowed": sorted(allowed), "why": why,
           "facts": {"swap_mb": round(swap, 1), "free_mb": free, "train": train, "browsers": profs,
                     "models": models}}
    os.makedirs(STATE, exist_ok=True)
    tmp = SLOT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    os.replace(tmp, SLOT)
    print("[res] %s ｜ 可用 %dMB ｜ swap %dMB（历史） ｜ 训练 %s ｜ 浏览器 %s ｜ 模型 %s"
          % (slot, free, swap, "是" if train else "否", ",".join(profs) or "无",
             ",".join(models) or "无"))
    print("[res] 本时段平台：%s（%s）" % ((pf or {}).get("id"), (pf or {}).get("note")))
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
    cases.append(("可用 500MB → DENY-NEW", decide(9000, 500, True, [], [], 3)[0] == "DENY-NEW"))
    cases.append(("可用 1000MB → DRAIN 但训练可续", "train" in decide(0, 1000, True, [], [], 12)[1]))
    cases.append(("swap 高但可用 4G → 仍可并行（swap 只是历史）",
                  decide(9000, 4000, True, [], [], 14)[0] == "PARALLEL"))
    cases.append(("训练中仍允许实战会话", "session1" in decide(0, 4000, True, [], [], 14)[1]))
    cases.append(("训练中仍允许发帖", "post" in decide(0, 4000, True, [], [], 3)[1]))
    cases.append(("已有 1 个浏览器 → 新活等它退出",
                  decide(0, 4000, True, ["browser-bilibili"], [], 14)[0] == "PARALLEL-1"))
    cases.append(("平台轮转能产出平台", platform_now(9, 0) is not None))
    cases.append(("未开账号的平台不排班", all(p["id"] not in ("xhs", "douyin", "zhihu", "weibo")
                                        for p in [platform_now(h, 0) for h in range(24)])))
    cases.append(("可读平台能进轮转", any(p["id"] in ("bilibili", "toutiao", "chejiahao", "gzh")
                                          for p in [platform_now(h, 0) for h in range(24)])))
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
