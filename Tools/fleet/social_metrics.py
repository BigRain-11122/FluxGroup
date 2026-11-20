#!/usr/bin/env python3
"""social_metrics.py — 只出数字：训练了几轮、长进多少、发了多少、评论多少。

一条命令回答"到底产出了什么"，不解释过程、不报告问题。
用法：python3 Tools/fleet/social_metrics.py [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TRAIN = os.path.join(SOCIAL, "train")
BAKED = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
OWN_PRACTICE = os.path.join(SOCIAL, "corpus", "human", "own_practice.jsonl")


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def train_metrics():
    led = rows(os.path.join(TRAIN, "TRAIN-LOOP-LEDGER.jsonl"))
    keep = [r for r in led if r.get("verdict") == "KEEP"]
    rej = [r for r in led if r.get("verdict") == "REJECT"]
    gains = [(r.get("lora_avg") or 0) - (r.get("base_avg") or 0) for r in keep]
    best = {}
    for r in keep:
        g = (r.get("lora_avg") or 0) - (r.get("base_avg") or 0)
        if r.get("seg") and g > best.get(r["seg"], (-99, ""))[0]:
            best[r["seg"]] = (round(g, 1), r.get("adapter") or "")
    runs = 0
    try:
        runs = len([d for d in os.listdir(os.path.join(TRAIN, "RUNS"))
                    if os.path.isdir(os.path.join(TRAIN, "RUNS", d))])
    except Exception:
        pass
    return {"runs": runs, "keep": len(keep), "reject": len(rej),
            "avg_gain": round(sum(gains) / len(gains), 1) if gains else 0,
            "max_gain": round(max(gains), 1) if gains else 0,
            "best_by_seg": {k: v[0] for k, v in sorted(best.items(), key=lambda x: -x[1][0])}}


def corpus_metrics():
    n = p = own = 0
    if os.path.exists(BAKED):
        for r in rows(BAKED):
            n += 1
            if (r.get("verdict") or "PASS") == "PASS":
                p += 1
                if r.get("src") == "own_practice":
                    own += 1
    return {"rows": n, "pass": p, "own_practice": own}


def action_metrics():
    led = rows(os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl"))
    c = collections.Counter(r.get("action") for r in led)
    today = datetime.now().strftime("%Y-%m-%d")
    ct = collections.Counter(r.get("action") for r in led
                             if str(r.get("ts", "")).startswith(today))
    return {"all": dict(c), "today": dict(ct)}


def practice_metrics():
    led = rows(os.path.join(SOCIAL, "practice-log.jsonl"))
    posts = [r for r in led if r.get("action") == "post"]
    ok = [r for r in posts if str(r.get("ok")).lower() == "true"]
    fails = [r for r in led if r.get("action") == "fail"]
    today = datetime.now().strftime("%Y-%m-%d")
    posts_today = [r for r in posts if str(r.get("ts", "")).startswith(today)]
    return {"posts_all": len(posts), "posts_ok": len(ok), "posts_today": len(posts_today),
            "fails": len(fails)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    m = {"train": train_metrics(), "corpus": corpus_metrics(),
         "actions": action_metrics(), "practice": practice_metrics()}
    if a.json:
        print(json.dumps(m, ensure_ascii=False, indent=1))
        return 0
    t, c, ac, pr = m["train"], m["corpus"], m["actions"], m["practice"]
    print("训练：%d 轮　留档 %d 件　淘汰 %d 件　平均 +%.1f 分　最高 +%.1f 分"
          % (t["runs"], t["keep"], t["reject"], t["avg_gain"], t["max_gain"]))
    if t["best_by_seg"]:
        print("  分段最高增益：" + "  ".join("%s %+.1f" % (k, v)
                                       for k, v in list(t["best_by_seg"].items())[:6]))
    print("语料：%d 行　可用 PASS %d 条　其中我们自己写的 %d 条"
          % (c["rows"], c["pass"], c["own_practice"]))
    print("账号动作（累计）：场 %d　看 %d　赞 %d　弹幕 %d　评论 %d"
          % (ac["all"].get("session", 0), ac["all"].get("watch", 0),
             ac["all"].get("like", 0), ac["all"].get("danmaku", 0),
             ac["all"].get("comment", 0)))
    print("账号动作（今天）：场 %d　看 %d　赞 %d　弹幕 %d　评论 %d"
          % (ac["today"].get("session", 0), ac["today"].get("watch", 0),
             ac["today"].get("like", 0), ac["today"].get("danmaku", 0),
             ac["today"].get("comment", 0)))
    print("实发评论：累计 %d 条（成功 %d）　今天 %d 条　出稿失败 %d 次"
          % (pr["posts_all"], pr["posts_ok"], pr["posts_today"], pr["fails"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
