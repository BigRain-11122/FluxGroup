#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""copy_compliance.py - 对外文案合规闸（广告法/导流/AIGC 标识/儿童/金融承诺）。

Why（2026-11-13）：PROD-BIGDOMAIN-MATERIAL 的「合规检查」长期 TOOL-PENDING，
但这类闸不该每上线一次重写一次——它对所有对外材料都成立（域名/算力/游戏/漫剧）。

判据只认可复算规则，不做"读起来像不像"的主观判断：
  B1 极限词（广告法第九条禁止的绝对化用语）
  B2 承诺/收益保证（金融与效果类，最易踩）
  B3 平台导流（微信号/二维码/外链，本集团一律不出现在内容里）
  B4 AIGC 标识（涉及 AI 生成内容时必须显著标注）
  B5 未成年人相关（面向儿童的内容需额外提示）
  B6 涉他方权利（明星姓名/品牌商标，只报警不判死）

输出：cph4/fleet/out/bigdomain/compliance.json
     {pass, violations:[{rule,level,line,snippet,why}], counts}

用法：
  python3 Tools/fleet/copy_compliance.py --text cph4/fleet/out/bigdomain/copy.md
  python3 Tools/fleet/copy_compliance.py --self-test
返回码：0 通过 / 2 有 HIGH 违规 / 3 输入缺失
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_OUT = os.path.join(ROOT, "cph4", "fleet", "out", "bigdomain", "compliance.json")

# 每条规则：命中即算，不做语感判断。词表故意宽，宁可多报给人看。
RULES = [
    {"id": "B1", "level": "HIGH", "why": "广告法禁止绝对化用语",
     "words": ["最好", "最强", "第一", "唯一", "顶级", "国家级", "世界级",
               "史上最", "绝无仅有", "万能", "永久"]},
    {"id": "B2", "level": "HIGH", "why": "收益/效果承诺，无法举证且易构成虚假宣传",
     "words": ["保证赚", "稳赚", "保本", "零风险", "必赚", "包过", "100%成功",
               "保证收益", "无风险"]},
    {"id": "B3", "level": "HIGH", "why": "内容内导流违反多数平台规则",
     "patterns": [r"加V", r"加微信", r"微信号", r"公众号[:：]", r"扫码",
                  r"二维码", r"https?://[^\s]+\?[^\s]*(utm|ref)="]},
    {"id": "B4", "level": "HIGH", "why": "AI 生成内容须显著标识",
     "require_if": ["AI生成", "AI 生成", "生成式", "合成画面"],
     # require 只认"显式标识"表述，不能把裸 "AI生成" 也算标识——否则
     # "本页由 AI生成 制作"这种没有标识的句子会被自己判成已标注（首版实测）。
     "require": ["AI 生成", "人工智能生成", "AI 生成内容", "已标注"]},
    {"id": "B5", "level": "MED", "why": "涉及未成年人需额外合规提示",
     "words": ["儿童", "小学生", "幼儿园", "未成年人", "孩子"]},
    {"id": "B6", "level": "MED", "why": "涉他方姓名/商标，需权利确认（只报警不判死）",
     "patterns": [r"刘德华", r"周杰伦", r"迪士尼", r"任天堂", r"米老鼠",
                  r"奥特曼", r"宝可梦"]},
]


def _scan_line(ln):
    """对单行跑全部规则，返回命中列表。"""
    hits = []
    for r in RULES:
        if r["id"] == "B4":
            continue                      # 需要全篇判断，逐行会误报
        for w in r.get("words") or []:
            if w in ln:
                hits.append({"rule": r["id"], "level": r["level"], "why": r["why"],
                             "snippet": w, "line": ln.strip()[:120]})
        for pat in r.get("patterns") or []:
            m = re.search(pat, ln)
            if m:
                hits.append({"rule": r["id"], "level": r["level"], "why": r["why"],
                             "snippet": m.group(0)[:40], "line": ln.strip()[:120]})
    return hits


def check(text):
    """纯函数：文案 -> 结论。可自检、可复算。"""
    lines = str(text or "").splitlines()
    violations = []
    for ln in lines:
        violations.extend(_scan_line(ln))

    # B4 全篇判断：出现生成类表述却没有标识 -> 一条 HIGH
    joined = "\n".join(lines)
    need = RULES[3].get("require_if") or []
    if need and any(k in joined for k in need):
        if not any(k in joined for k in RULES[3]["require"]):
            violations.append({"rule": "B4", "level": "HIGH",
                               "why": "出现 AI 生成类表述但全文无显著 AI 标识",
                               "snippet": "缺标识", "line": "（全篇）"})
    # 去重（同一行同一规则同一片段只报一次）
    seen, uniq = set(), []
    for v in violations:
        k = (v["rule"], v["snippet"], v["line"][:40])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(v)
    counts = {}
    for v in uniq:
        counts[v["level"]] = counts.get(v["level"], 0) + 1
    high = counts.get("HIGH", 0)
    return {"pass": high == 0, "violations": uniq, "counts": counts,
            "lines": len(lines), "checked_at": datetime.now().isoformat(timespec="seconds"),
            "note": ("HIGH=0 才可通过；MED 需人工确认后放行" if high == 0
                     else "有 HIGH 违规，禁止对外使用")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=os.path.join(ROOT, "cph4", "fleet", "out",
                                                   "bigdomain", "copy.md"))
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not os.path.exists(a.text):
        print("缺输入：%s（先产出文案，再做合规检查）" % a.text)
        return 3
    text = open(a.text, encoding="utf-8", errors="replace").read()
    rep = check(text)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    print("合规检查 -> %s｜%d 行｜HIGH %d / MED %d｜%s"
          % (a.out, rep["lines"], rep["counts"].get("HIGH", 0),
             rep["counts"].get("MED", 0), "通过" if rep["pass"] else "不通过"))
    return 0 if rep["pass"] else 2


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    clean = "# 平台介绍\n\n这是一个面向独立开发者的工具平台。\n支持文本处理与批量生成。"
    r = check(clean)
    chk("干净文案 -> 通过", r["pass"] and not r["violations"], r)
    chk("空文案 -> 通过（无内容无违规）", check("")["pass"])
    chk("极限词 -> HIGH 且不通过", not check("我们是最好的平台")["pass"])
    chk("收益承诺 -> HIGH", not check("加入即稳赚，保本无风险")["pass"])
    chk("导流 -> HIGH（微信号）", not check("详情加微信 abc123")["pass"])
    chk("带参数外链 -> HIGH", not check("报名 https://x.com/a?utm=1")["pass"])
    chk("AI 表述但无标识 -> HIGH",
        not check("本页图片由 AI生成 技术制作")["pass"])
    chk("AI 表述且有标识 -> 通过",
        check("本页图片为 AI 生成，已标注")["pass"])
    chk("儿童相关内容 -> MED（可放行但需人确认）",
        check("适合儿童阅读的绘本")["counts"].get("MED", 0) >= 1)
    chk("明星姓名 -> MED 报警",
        check("致敬周杰伦的经典旋律")["counts"].get("MED", 0) >= 1)
    chk("同句重复命中只算一次",
        len([v for v in check("最好最好最好")["violations"] if v["snippet"] == "最好"]) == 1)
    chk("结论可复算（同输入两次一致）",
        {k: v for k, v in check(clean).items() if k != "checked_at"} ==
        {k: v for k, v in check(clean).items() if k != "checked_at"})
    print("\n[copy_compliance] %d/%d" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
