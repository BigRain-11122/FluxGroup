#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""situation_audit.py - 未知情况登记册的核验器（防"写在表里就当解决了"）。

读 cph4/fleet/SITUATION-REGISTRY-v1.json，做三件事：
  1 复算次数：从队列全史 / 回执 / 堵点台账 / 经验台账重新数，不采信手填的数字
  2 核落点：每条情况声称的 landing 文件必须真在盘（少一个就是 GAP）
  3 出结论：CLOSED / OPEN / GAP，并按"最严重的先列"排序

状态规则：
  GAP    声称 CLOSED 但落点核验不到（最严重，等于假绿）
  OPEN   没有 landing，或状态自报 OPEN
  CLOSED 落点在盘且状态自报 CLOSED

用法：
  python3 Tools/fleet/situation_audit.py
  python3 Tools/fleet/situation_audit.py --write   # 同时写 cph4/fleet/SITUATION-CLOSURE.md
  python3 Tools/fleet/situation_audit.py --self-test
返回码：0 全 CLOSED / 1 有 OPEN / 2 有 GAP / 3 自检失败
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")


def _json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def load_corpus(root=None):
    rroot = root or ROOT
    fdir = os.path.join(rroot, "cph4", "fleet")
    cards = {}
    for p in (glob.glob(os.path.join(fdir, "rt", "*", "queue.jsonl"))
              + [os.path.join(fdir, "PRODUCTION-QUEUE.jsonl")]
              + glob.glob(os.path.join(fdir, "queue-archive*.jsonl"))
              + glob.glob(os.path.join(fdir, "storage", "archive", "rt-*", "*.jsonl"))
              + glob.glob(os.path.join(fdir, "storage", "archive", "*.jsonl"))):
        for r in _rows(p):
            if isinstance(r, dict) and r.get("id"):
                cards[str(r["id"])] = r
    receipts = []
    for p in glob.glob(os.path.join(fdir, "queue-receipts", "*.json")):
        d = _json(p, [])
        if isinstance(d, list):
            receipts.extend([x for x in d if isinstance(x, dict)])
        elif isinstance(d, dict):
            receipts.append(d)
    blockers = _rows(os.path.join(fdir, "state", "blocker-ledger.jsonl"))
    lessons = _rows(os.path.join(fdir, "LESSONS-LEDGER.jsonl"))
    return {"cards": list(cards.values()), "receipts": receipts,
            "blockers": blockers, "lessons": lessons}


def count_evidence(ev, corpus):
    """按证据描述重新数一遍。数不出来返回 None（不猜）。"""
    try:
        if ev.get("src") == "queue":
            field, val = ev.get("field"), ev.get("equals")
            starts = ev.get("starts")
            n = 0
            for c in corpus["cards"]:
                v = c.get(field)
                if v is None:
                    continue
                if starts and str(v).strip().startswith(starts):
                    n += 1
                elif val is not None and str(v) == str(val):
                    n += 1
            return n
        if ev.get("src") == "receipts":
            field, val = ev.get("field"), ev.get("equals")
            return sum(1 for r in corpus["receipts"] if str(r.get(field)) == str(val))
        if ev.get("src") == "blockers":
            cls = ev.get("class")
            return sum(1 for r in corpus["blockers"] if r.get("class") == cls)
        if ev.get("src") == "lessons":
            cls = ev.get("class")
            return sum(1 for r in corpus["lessons"] if r.get("class") == cls)
    except Exception:
        return None
    return None


def audit(reg, root=None, corpus=None):
    rroot = root or ROOT
    corpus = corpus if corpus is not None else load_corpus(root)
    out = []
    for s in reg.get("situations") or []:
        counts = []
        for ev in s.get("evidence") or []:
            n = count_evidence(ev, corpus)
            if n is not None:
                counts.append(n)
        landing = s.get("landing") or []
        missing = [p for p in landing if not os.path.exists(os.path.join(rroot, p))]
        claim = (s.get("status") or "OPEN").upper()
        if claim == "CLOSED" and (not landing or missing):
            status = "GAP"
        elif claim == "CLOSED":
            status = "CLOSED"
        else:
            status = "OPEN"
        out.append({"id": s.get("id"), "name": s.get("name"), "symptom": s.get("symptom"),
                    "rule": s.get("rule"), "old_gap": s.get("old_gap"),
                    "counts": counts, "count": max(counts) if counts else None,
                    "landing": landing, "missing": missing, "status": status,
                    "claim": claim})
    return out


def render(rows, extra=None):
    order = {"GAP": 0, "OPEN": 1, "CLOSED": 2}
    rows = sorted(rows, key=lambda r: (order.get(r["status"], 9), -(r["count"] or 0)))
    lines = ["# 未知情况闭环表（自动生成，勿手改）", "",
             "> 生成器=`Tools/fleet/situation_audit.py`；登记册=`SITUATION-REGISTRY-v1.json`。",
             "> 状态：CLOSED=落点在盘 / OPEN=规则已定但无可执行落点 / GAP=声称已闭环却核验不到。",
             ""]
    if extra:
        lines += extra + [""]
    lines += ["| 编号 | 情况 | 实测次数 | 旧漏在哪 | 新规则 | 状态 |",
              "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | **%s** |" % (
            r["id"], r["name"], "-" if r["count"] is None else r["count"],
            (r["old_gap"] or "")[:40], (r["rule"] or "")[:60], r["status"]))
    bad = [r for r in rows if r["status"] in ("GAP", "OPEN")]
    lines += ["", "## 未闭环清单（要先做这些）", ""]
    if not bad:
        lines.append("（无）")
    for r in bad:
        if r["status"] == "GAP":
            why = "落点缺失: " + ",".join(r["missing"])
        elif not r["landing"]:
            why = "还没有可执行落点"
        else:
            why = "规则已定、落点在盘，但缺可复算判据/演练"
        lines.append("- **%s %s**：%s" % (r["id"], r["name"], why))
    return "\n".join(lines) + "\n"


def self_test():
    import tempfile
    ok = total = 0

    def chk(name, cond):
        nonlocal ok, total
        total += 1
        ok += 1 if cond else 0
        print("%s %s" % ("ok  " if cond else "FAIL", name))

    corpus = {"cards": [{"id": "1", "cancel_reason": "坏卡闭环：x"},
                        {"id": "2", "cancel_reason": "迁移作废"}],
              "receipts": [{"rc": None}, {"rc": 0}],
              "blockers": [{"class": "STAGE-STALE"}, {"class": "STAGE-STALE"}],
              "lessons": []}
    reg = {"situations": [
        {"id": "A", "name": "a", "status": "CLOSED", "landing": ["Tools/fleet/voice_gate.py"],
         "evidence": [{"src": "queue", "field": "cancel_reason", "starts": "坏卡闭环"}]},
        {"id": "B", "name": "b", "status": "CLOSED", "landing": ["nope/missing.py"]},
        {"id": "C", "name": "c", "status": "OPEN", "landing": []},
    ]}
    rows = audit(reg, ROOT, corpus)
    d = {r["id"]: r for r in rows}
    chk("次数复算正确", d["A"]["count"] == 1)
    chk("落点在盘 -> CLOSED", d["A"]["status"] == "CLOSED")
    chk("声称闭环但落点缺失 -> GAP", d["B"]["status"] == "GAP")
    chk("自报 OPEN -> OPEN", d["C"]["status"] == "OPEN")
    txt = render(rows)
    chk("表格里 GAP 排在 CLOSED 前", txt.index("**GAP**") < txt.index("**CLOSED**"))

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "cph4", "fleet"))
        rows2 = audit(reg, td, corpus)
        chk("根目录不同 -> A 也变 GAP（不认死路径）",
            [r["status"] for r in rows2 if r["id"] == "A"][0] == "GAP")

    print("[situation_audit] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    rroot = a.root or ROOT
    reg = _json(os.path.join(rroot, "cph4", "fleet", "SITUATION-REGISTRY-v1.json"), {})
    corpus = load_corpus(rroot)
    rows = audit(reg, rroot, corpus)
    stat = collections.Counter(r["status"] for r in rows)
    summary = ["## 统计面", "",
               "- 登记情况 **%d** 种；卡片全史 **%d** 张（去重）；回执 **%d** 份；堵点台账 **%d** 条；经验 **%d** 条" % (
                   len(rows), len(corpus["cards"]), len(corpus["receipts"]),
                   len(corpus["blockers"]), len(corpus["lessons"])),
               "- CLOSED **%d** / OPEN **%d** / GAP **%d**" % (
                   stat.get("CLOSED", 0), stat.get("OPEN", 0), stat.get("GAP", 0))]
    txt = render(rows, summary)
    if a.write:
        p = os.path.join(rroot, "cph4", "fleet", "SITUATION-CLOSURE.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        print("[situation_audit] 写入 %s" % p)
    print(txt)
    if stat.get("GAP"):
        return 2
    if stat.get("OPEN"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
