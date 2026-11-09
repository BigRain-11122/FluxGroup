#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""conflict_marker_scrub.py - 剥离误提交进仓的 git 冲突标记（机队卫生工具）。

来历：QUEUE-CONFLICT-RESOLVE-20261108.md 记载，产物卡曾把**未解决的冲突块**提交进
origin（触发 CONFLICT-MARKER-GATE 阻塞全仓提交）。人工并列保留两侧报告对 md 可行，
但对 JSON/JSONL 是毒药——文件直接不可解析（2026-11-09 合并时实测 19 个审计 JSON 损坏）。

规则（保守，只处理标记块本身）：
  · `<<<<<<< ... =======` 之间 = ours（旧时间戳侧），丢弃；
  · `======= ... >>>>>>>` 之间 = theirs（更新侧），保留；
  · 剥完后 JSON/JSONL 必须可解析，解析失败的文件保持原样并报告（交人工）。
用法：python3 Tools/fleet/conflict_marker_scrub.py [--dry] [路径前缀...]
"""
import glob
import json
import os
import sys


def scrub_text(text):
    """返回 (新文本, 处理块数)。策略=保留 theirs 侧。"""
    lines = text.split("\n")
    out, i, blocks = [], 0, 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("<<<<<<< "):
            blocks += 1
            # skip ours side
            i += 1
            while i < len(lines) and not lines[i].startswith("======="):
                i += 1
            i += 1                       # pass =======
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                out.append(lines[i])     # keep theirs
                i += 1
            i += 1                       # pass >>>>>>>
            continue
        out.append(ln)
        i += 1
    return "\n".join(out), blocks


def valid(path, text):
    if path.endswith(".json"):
        try:
            json.loads(text); return True
        except Exception:
            return False
    if path.endswith(".jsonl"):
        for l in text.splitlines():
            if l.strip():
                try:
                    json.loads(l)
                except Exception:
                    return False
    return True      # md/其他：不强制


def main():
    dry = "--dry" in sys.argv
    pats = [a for a in sys.argv[1:] if a != "--dry"] or ["cph4", "Tools", "docs"]
    files = []
    for p in pats:
        if os.path.isdir(p):
            for ext in ("json", "jsonl", "md"):
                files += glob.glob(os.path.join(p, "**", "*." + ext), recursive=True)
        else:
            files.append(p)
    fixed = broken = 0
    for f in sorted(set(files)):
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                t = fh.read()
        except Exception:
            continue
        if "<<<<<<< " not in t:
            continue
        new, n = scrub_text(t)
        if "<<<<<<< " in new:
            print("留人工（剥后仍有标记）:", f); broken += 1; continue
        if not valid(f, new):
            print("留人工（剥后 JSON 仍坏）:", f); broken += 1; continue
        fixed += 1
        print("%s: 剥离 %d 块%s" % (f, n, "" if dry else " -> 已清洗"))
        if not dry:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
    print("[scrub] fixed=%d need_human=%d dry=%s" % (fixed, broken, dry))
    return 0 if broken == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
