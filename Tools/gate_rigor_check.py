# -*- coding: utf-8 -*-
"""gate_rigor_check.py - 标准/闸的严谨性体检（六问）。

为什么要有它：2026-11-03 的音色闸第一版把阈值拍了出来（44.1k/SNR30/底噪-55），
用 10 条真实素材一验，10/10 全判负 = 废闸。同类病在 ai_smell_gate 首版也发生过
（判死 32 张真人）。病根不是不会写闸，是**写闸前没被追问**。

grill-with-docs 那类技能用"逐轮问人"解决这件事，但那会引入等待点（CEO 明令不设卡点）。
所以这里把它变成机器自检：每个标准/闸文档必须能回答六问，缺哪问直接点名。

六问（全部可机判）：
1. 标定依据  —— 阈值从哪来？要有「标定/实测/分位/样本」+ 数字
2. 负控/反例 —— 有没有「应拒绝」样例？要有「负控/selftest/反例/应拒绝」
3. 能力边界  —— 判不了什么？要有「判不了/边界/局限/未实现/不适用」
4. 唯一判据  —— 指向哪个工具？要有 Tools/xxx.py 或 python 命令行
5. 失效条件  —— 什么时候不算数？要有「失效/例外/仅在/前提」
6. 验证记录  —— 真跑过吗？要有「已验/正反/对照/实测结果」

用法：
  python Tools/gate_rigor_check.py --dir cph4/fleet --glob "*LAW*.md" ...
  python Tools/gate_rigor_check.py --all          # 扫默认位置
退出码：0 全过；2 有缺项；3 输入缺失
"""
import argparse
import glob as globmod
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHECKS = [
    ("标定依据", [r"标定", r"实测", r"分位", r"样本"], r"\d"),
    ("负控/反例", [r"负控", r"selftest", r"自检", r"反例", r"应拒绝", r"判负"], None),
    ("能力边界", [r"判不了", r"边界", r"局限", r"未实现", r"不适用", r"测不准"], None),
    ("唯一判据", [r"Tools[/\\][\w.-]+\.py", r"python\s+Tools"], None),
    ("失效条件", [r"失效", r"例外", r"仅在", r"前提", r"触发条件"], None),
    ("验证记录", [r"已验", r"正反", r"对照", r"验证表", r"实测结果"], None),
]


def judge(path):
    try:
        text = io.open(path, encoding="utf-8").read()
    except Exception as e:
        return {"file": path, "error": str(e), "miss": ["读不了"]}
    miss = []
    for name, words, extra in CHECKS:
        hit = any(re.search(w, text, re.I) for w in words)
        if hit and extra and not re.search(extra, text):
            hit = False
        if not hit:
            miss.append(name)
    return {"file": os.path.relpath(path, ROOT), "miss": miss,
            "lines": len(text.splitlines()), "bytes": len(text.encode("utf-8"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dir", action="append", default=[])
    ap.add_argument("--glob", action="append", default=[])
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    dirs = a.dir or ([os.path.join(ROOT, "cph4", "fleet")] if a.all else [])
    pats = a.glob or (["*LAW*.md", "QC-*.md", "*-SPEC-*.md", "*SPEC-v*.md",
                       "QUALITY-*.md", "CANON-v*.md"] if a.all else [])
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            print("BLOCKED dir missing: %s" % d)
            return 3
        for p in pats:
            files += globmod.glob(os.path.join(d, "**", p), recursive=True)
    files = sorted(set(files))
    if not files:
        print("BLOCKED no candidate docs (dirs=%s pats=%s)" % (dirs, pats))
        return 3

    rows = [judge(f) for f in files]
    bad = [r for r in rows if r.get("miss")]
    w = max(len(r["file"]) for r in rows)
    for r in rows:
        mark = "OK  " if not r["miss"] else "GAP "
        print("%s %-*s 缺：%s" % (mark, w, r["file"],
                                  "—" if not r["miss"] else "、".join(r["miss"])))
    print("\n共 %d 份，六问齐 %d，有缺 %d" % (len(rows), len(rows) - len(bad), len(bad)))
    if bad:
        print("注：GAP≠闸坏了，是这份标准还答不出六问之一；补问比补闸便宜。")

    if a.json:
        import json
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump({"rows": rows, "bad": [r["file"] for r in bad],
                   "checked_at": __import__("datetime").datetime.now().isoformat(timespec="seconds")},
                  io.open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())