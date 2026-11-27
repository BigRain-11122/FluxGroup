#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_train.py - 养号话术的训练度量：批量生成 → 闸校验 → 按类型看失败。

Why（2026-11-13 CEO「好好训练养号相关技能和话术」）：
「训练」在本地 4B 语境下不是微调，而是**语料 → few-shot → 生成 → 闸 → 定位失败类型**的循环。
没有度量就没有训练：改完提示词只说"感觉好点了"，等于没改。

判据沿用 voice_gate（唯一权威），这里只做批量与归类：
  * 内置 20 类合成评论（不是真实用户数据，仅作回归样本，标注 synthetic）；
  * 红线类（AI/身份/法务/广告）要求**草稿为空**，给了草稿算失败；
  * 其余类别要求草稿非空且过闸；
  * 输出按类别的通过/失败与失败原因，便于针对性改语料或提示词。

用法：
    python3 Tools/fleet/voice_train.py                # 跑全量并打印
    python3 Tools/fleet/voice_train.py --json          # 机器可读
    python3 Tools/fleet/voice_train.py --self-test
返回码：0 全过 / 1 有失败 / 3 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

# 20 类合成回归样本（synthetic，不代表真实用户；覆盖好写的与最容易写坏的）
CASES = [
    ("praise", "女主好美"),
    ("praise", "这段剪辑太顺了"),
    ("praise", "up主辛苦了"),
    ("question", "BGM叫什么"),
    ("question", "这歌叫什么名字 找好久了"),
    ("question", "用什么软件剪的"),
    ("question", "第三集啥时候更啊"),
    ("question", "能出个系列吗"),
    ("complaint", "后面太赶了，是不是砍了"),
    ("complaint", "这期广告味有点重"),
    ("complaint", "画质有点糊"),
    ("complaint", "这个转场有点生硬"),
    ("emotion", "看哭了"),
    ("emotion", "哈哈哈这什么鬼"),
    ("emotion", "已三连"),
    ("legal", "这不就是抄某某MV吗"),
    ("question_ai", "这画面是AI做的吗"),
    ("question_identity", "up主是男是女"),
    ("spam", "加V看更多精彩内容"),
    ("flame", "什么垃圾东西"),
]
REDLINE = {"legal", "question_ai", "question_identity", "spam", "flame"}


def gate(text, ctx):
    p = subprocess.run([sys.executable, os.path.join(HERE, "voice_gate.py"),
                        "--text", text, "--face", "comment", "--ctx", ctx],
                       capture_output=True, text=True)
    try:
        d = json.loads((p.stdout or "").strip().splitlines()[-1])
    except Exception:
        d = {"verdict": "ERROR", "hits": [(p.stderr or "")[:80]]}
    return d


def run_once(dry=False):
    import social_drafts as sd
    rows = []
    for kind_hint, ctx in CASES:
        if dry:
            rows.append({"ctx": ctx, "hint": kind_hint, "kind": None, "draft": "",
                         "gate": {"verdict": "SKIP"}, "ok": None})
            continue
        try:
            # classify_and_draft 返回 (kind, draft, needs_human, note)
            kind, draft, _needs, _note = sd.classify_and_draft(ctx)
        except Exception as e:
            rows.append({"ctx": ctx, "hint": kind_hint, "kind": "ERR", "draft": "",
                         "gate": {"verdict": "ERROR", "hits": [type(e).__name__]}, "ok": False})
            continue
        draft = (draft or "").strip()
        if kind in REDLINE or kind_hint in REDLINE:
            ok = (draft == "")
            g = {"verdict": "EMPTY-OK" if ok else "SHOULD-BE-EMPTY"}
        else:
            if not draft:
                ok, g = False, {"verdict": "EMPTY", "hits": ["该给草稿却留空"]}
            else:
                g = gate(draft, ctx)
                ok = g.get("verdict") == "PASS"
        rows.append({"ctx": ctx, "hint": kind_hint, "kind": kind,
                     "draft": draft, "gate": g, "ok": ok})
    return rows


def summary(rows):
    ok = [r for r in rows if r["ok"]]
    bad = [r for r in rows if not r["ok"]]
    by = {}
    for r in bad:
        by.setdefault(r["hint"], []).append(
            {"ctx": r["ctx"], "draft": r["draft"],
             "why": (r["gate"].get("hits") or [r["gate"].get("verdict")])[:2]})
    return {"total": len(rows), "pass": len(ok), "fail": len(bad),
            "rate": round(100.0 * len(ok) / max(1, len(rows)), 1), "fail_by_kind": by}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rows = run_once(dry=a.dry)
    s = summary(rows)
    if a.json:
        print(json.dumps({"summary": s, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        print("== 养号话术回归：%d/%d 通过（%.1f%%）==" % (s["pass"], s["total"], s["rate"]))
        for r in rows:
            mark = "ok  " if r["ok"] else "FAIL"
            print("  %s %-18s %-12s %s" % (mark, r["ctx"][:18], r["kind"],
                                           (r["draft"] or "（空）")[:30]))
        if s["fail_by_kind"]:
            print("\n按类型定位失败：")
            for k, v in s["fail_by_kind"].items():
                print("  [%s] %d 例" % (k, len(v)))
                for x in v[:2]:
                    print("     %s → %s | %s" % (x["ctx"][:16], (x["draft"] or "空")[:24], x["why"]))
    return 0 if s["fail"] == 0 else 1


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    chk("用例覆盖 20 类", len(CASES) == 20, len(CASES))
    chk("红线类都在列表里",
        set(REDLINE).issubset({h for h, _ in CASES}))
    # 汇总逻辑：人为造三行
    rows = [{"ok": True, "hint": "praise", "gate": {}, "ctx": "a", "draft": "x"},
            {"ok": False, "hint": "question", "gate": {"verdict": "BLOCK",
                                                       "hits": ["空承诺"]},
             "ctx": "b", "draft": "我会尽快"},
            {"ok": False, "hint": "question", "gate": {"verdict": "BLOCK",
                                                       "hits": ["客服腔"]},
             "ctx": "c", "draft": "感谢喜爱"}]
    s = summary(rows)
    chk("通过率算对", s["rate"] == 33.3, s["rate"])
    chk("失败按类型归类", "question" in s["fail_by_kind"] and
        len(s["fail_by_kind"]["question"]) == 2)
    chk("失败带原因", s["fail_by_kind"]["question"][0]["why"])
    # 闸真能拦：直接验一条坏话术
    g = gate("感谢喜爱！具体手法已整理在置顶笔记中", "转场怎么做的")
    chk("负控：闸必须拦住编造+客服腔", g.get("verdict") != "PASS", g)
    print("\n[voice_train] %d/%d" % (ok, total))
    return 0 if ok == total else 3


if __name__ == "__main__":
    sys.exit(main())
