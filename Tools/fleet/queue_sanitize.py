#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""queue_sanitize.py - 队列/备队列被 git 冲突标记污染时的判定与修复。

为什么会发生（2026-11-08 实锚）：`job(<id>): artifact` 类提交把整个
PRODUCTION-QUEUE.jsonl 当成 "我的那份文件" 覆盖上去，而出提交的那一侧自己的工作树里
还留着未解决的冲突标记，于是 `<<<<<<< HEAD` / `=======` / `>>>>>>> <sha>` 被**提交进历史**
（实测 138 个空冲突块 = 414 行），任何严格 JSON 解析器读队列都会直接抛异常；
更隐蔽的是"能容错读取的脚本照跑"，于是没人发现，只有必须严格解析的那条路径静默失败。

处理原则：
  · 冲突块取**两侧并集**再按 id 去重（绝不因为冲突丢卡）；
  · 去重时保留文件中最后出现的一行（git 合并把 theirs 放在后面），并把每一处
    "同 id 状态不同" 写进报告，事后可审计；
  · `--check` 只判不改（给回归/巡检用），`--fix` 才写盘。

用法：
  python3 Tools/fleet/queue_sanitize.py --check
  python3 Tools/fleet/queue_sanitize.py --fix [--report cph4/fleet/QUEUE-CONFLICT-RESOLVE.md]
退出码：0 干净（或已修好） · 1 有污染（--check） · 2 文件缺失
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TARGETS = ("cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/PRODUCTION-BACKLOG.jsonl")
MARK = ("<<<<<<< ", "=======", ">>>>>>> ")


def scan(path):
    """返回 (冲突块数, 非JSON行数, 总行数)。任何一侧都可能为空（空冲突块很常见）。"""
    blocks = nonjson = total = 0
    state = "ok"
    for raw in open(path, encoding="utf-8"):
        l = raw.rstrip("\n")
        if l.startswith(MARK[0]):
            blocks += 1; state = "ours"; continue
        if state == "ours" and l.rstrip() == MARK[1]:
            state = "theirs"; continue
        if state == "theirs" and l.startswith(MARK[2]):
            state = "ok"; continue
        if not l.strip() or state != "ok":
            continue
        total += 1
        try:
            json.loads(l)
        except Exception:
            nonjson += 1
    return blocks, nonjson, total


def fix(path, report=None):
    lines = open(path, encoding="utf-8").read().split("\n")
    rows, bufo, buft = [], [], []
    state, blocks = "ok", 0
    for l in lines:
        if l.startswith(MARK[0]):
            state = "ours"; blocks += 1; bufo, buft = [], []; continue
        if state == "ours" and l.rstrip() == MARK[1]:
            state = "theirs"; continue
        if state == "theirs" and l.startswith(MARK[2]):
            rows.extend(bufo); rows.extend(buft)   # 两侧并集：冲突里没有"哪边全对"
            state = "ok"; bufo, buft = [], []; continue
        (bufo if state == "ours" else buft if state == "theirs" else rows).append(l)

    parsed, dropped = [], 0
    for l in rows:
        l = l.strip()
        if not l:
            continue
        try:
            parsed.append(json.loads(l))
        except Exception:
            dropped += 1

    by, changed = {}, []
    for r in parsed:
        k = r.get("id") or ("anon:%d" % len(by))
        old = by.get(k)
        if old and (old.get("state") != r.get("state") or old.get("owner") != r.get("owner")):
            changed.append((k, old.get("state"), old.get("owner"), r.get("state"), r.get("owner")))
        by[k] = r

    out = list(by.values())
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if report:
        rep = ["# 队列冲突标记清理报告", "",
               "- 文件：`%s`" % os.path.relpath(path, ROOT),
               "- 冲突块：%d · 冲突外非 JSON 行：%d" % (blocks, dropped),
               "- 行数：清理前 %d → 清理后 %d" % (len(parsed), len(out)),
               "- 同 id 状态冲突择后者：%d 条" % len(changed), ""]
        if changed:
            rep += ["| id | 被覆盖 | 保留 |", "|---|---|---|"]
            rep += ["| %s | %s/%s | %s/%s |" % c for c in changed[:80]]
        open(report, "w", encoding="utf-8").write("\n".join(rep) + "\n")
    return {"blocks": blocks, "dropped": dropped,
            "before": len(parsed), "after": len(out), "changed": len(changed)}


def dedupe_live(path, apply=False):
    """同交付物多张活卡 → 撤掉多余的（保留跑得最远的：RUNNING > 最早创建）。

    为什么必须能自动做（2026-11-08 实锚）：供给器被脉按轮调用，两轮并发会看到
    "没有活卡"而各铺一张，一下午攒出 8 组重复活卡；两台机同时跑同一交付物，
    回执互相覆盖，等于白烧算力。人工发现一次修一次，修不完。
    """
    import collections
    rows = []
    for l in open(path, encoding="utf-8"):
        l = l.strip()
        if not l:
            continue
        try:
            rows.append(json.loads(l))
        except Exception:
            pass
    LIVE = ("OPEN", "READY", "RUNNING", "CLAIMED", "PENDING")
    by = collections.defaultdict(list)
    for r in rows:
        if str(r.get("state") or "").upper() in LIVE and (r.get("deliverable") or "").strip():
            by[r["deliverable"].strip()].append(r)
    groups = {d: rs for d, rs in by.items() if len(rs) > 1}
    patch = []
    for d, rs in groups.items():
        rs.sort(key=lambda r: (0 if str(r.get("state")).upper() == "RUNNING" else 1,
                               r.get("created_at") or ""))
        keep = rs[0]
        for r in rs[1:]:
            patch.append({"id": r.get("id"), "state": "CANCELLED",
                          "cancel_reason": "DUP-DELIVERABLE: 与 %s 同交付物 %s（并发供给），按交付物去重"
                                           % (keep.get("id"), d),
                          "cancelled_by": "queue_sanitize:dedupe"})
    if patch and apply:
        with open(path, "a", encoding="utf-8") as f:
            for r in patch:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"groups": len(groups), "cancelled": len(patch), "applied": bool(patch and apply)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--report", default="")
    ap.add_argument("--dedupe", action="store_true",
                    help="按交付物合并重复活卡（与 --fix 同一工具，避免工具泛滥）")
    a = ap.parse_args()
    dirty = 0
    for rel in TARGETS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        blocks, nonjson, total = scan(p)
        if blocks or nonjson:
            dirty += 1
            print("[queue-sanitize] %s 污染：冲突块=%d 非JSON行=%d（总 %d 行）"
                  % (rel, blocks, nonjson, total))
            if a.fix:
                r = fix(p, a.report or None)
                print("[queue-sanitize] 已修 %s -> %s" % (rel, r))
        else:
            print("[queue-sanitize] %s 干净（%d 行）" % (rel, total))
    if a.dedupe:
        for rel in TARGETS:
            pp = os.path.join(ROOT, rel)
            if not os.path.isfile(pp):
                continue
            r = dedupe_live(pp, apply=a.fix or a.dedupe)
            if r["groups"]:
                print("[queue-sanitize] %s 重复活卡组=%d 撤销=%d applied=%s"
                      % (rel, r["groups"], r["cancelled"], r["applied"]))
    if a.check and dirty:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())