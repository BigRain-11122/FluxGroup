#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arch_perf.py — 原型效果台账：哪种说法真的有人买账（用平台反馈校准策略）。

创新点（2026-11-22 CEO「工作要有全面性创新性」）：
此前原型只是"均匀轮换"，谁好谁坏没人知道；唯一的外部反馈是回验时拿到的
**我们自己那条评论的点赞数**。本工具把它变成策略输入：

  qualified 行（rpid → 用的哪个原型）
  verify 行（rpid → 点赞数 / 是否可见）
      ↓
  ARCH-PERF.json：每个原型 n / 点赞中位 / 被赞率
      ↓
  llm_client._pick_arch：冷启动期均匀轮换；某原型样本≥5 后，
  20% 的候选改投"当前被赞率最高"的那个（探索-利用，防止一直交学费）

注意：只统计**已回验**的投稿，且样本不足时不下结论（避免 2 条 0 赞就把一整类打死）。
用法：python3 Tools/fleet/arch_perf.py [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOG = os.path.join(SOCIAL, "practice-log.jsonl")
OUT = os.path.join(STATE, "ARCH-PERF.json")
MIN_N = 5          # 少于 5 条不下结论


def _rows():
    out = []
    try:
        for line in open(LOG, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def build():
    rows = _rows()
    arch = {}
    for r in rows:
        if r.get("action") == "qualified" and r.get("rpid"):
            arch[str(r["rpid"])] = r.get("arch") or ""
    perf = {}
    for r in rows:
        if r.get("action") != "verify":
            continue
        rp = str(r.get("rpid") or "")
        a = arch.get(rp)
        if not a:
            continue
        p = perf.setdefault(a, {"n": 0, "likes": [], "visible": 0})
        p["n"] += 1
        if r.get("likes") is not None:
            p["likes"].append(int(r["likes"]))
        if r.get("visible") is True:
            p["visible"] += 1
    out = {}
    for a, p in perf.items():
        likes = p["likes"]
        out[a] = {
            "n": p["n"],
            "liked_rate": round(sum(1 for x in likes if x > 0) / len(likes), 3) if likes else None,
            "likes_median": round(st.median(likes), 1) if likes else None,
            "visible_rate": round(p["visible"] / p["n"], 3) if p["n"] else None,
            "confident": len(likes) >= MIN_N,
        }
    best, best_key = None, None
    for a, v in out.items():
        if not v["confident"]:
            continue
        k = (v["liked_rate"] or 0, v["likes_median"] or 0)
        if best_key is None or k > best_key:
            best, best_key = a, k
    doc = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
           "min_n": MIN_N, "best": best, "archetypes": out}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    if a.json:
        print(json.dumps(doc, ensure_ascii=False))
        return 0
    n = sum(v["n"] for v in doc["archetypes"].values())
    print("[perf] 已回验且带原型的投稿 %d 条；结论门槛 n≥%d" % (n, doc["min_n"]))
    for k, v in sorted(doc["archetypes"].items(), key=lambda kv: -(kv[1]["liked_rate"] or 0)):
        print("   %-9s n=%-3d 被赞率 %-6s 点赞中位 %-5s 可见率 %-6s %s" % (
            k, v["n"],
            "%.0f%%" % (100 * v["liked_rate"]) if v["liked_rate"] is not None else "—",
            v["likes_median"] if v["likes_median"] is not None else "—",
            "%.0f%%" % (100 * v["visible_rate"]) if v["visible_rate"] is not None else "—",
            "✅ 可下结论" if v["confident"] else "样本不足"))
    print("[perf] 当前最优原型：%s" % (doc["best"] or "样本不足，暂不倾斜"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
