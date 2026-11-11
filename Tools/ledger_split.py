#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""台账水位闸 + 分卷器（单工具双职责，机器判据替代人工承诺）。

用法：
  python Tools/ledger_split.py --check
      只读报告：docs/decisions.md / docs/orders.md 体量、最老块日期、是否过线。
      rc=0 全在线内；rc=1 有过线件（供夜轮/决策轮/值守轮任一班次直接判红）。
  python Tools/ledger_split.py --apply [--cut 2026-11-08]
      把早于 cut 的块/行移入档案卷（决策=整块按 ## 日期头；orders=整行按首列日期）。
      写前备份 <file>.bak-prediv；写后校验「新件字节+迁出字节=原件字节」，不等即抛错不落盘。

判据（2026-11-12 委员会第 58 批 D-20261112-04 增补）：
  decisions <= 200KB / orders <= 250KB；--check rc=1 即可被任何脚本当红消费。
"""
import argparse
import datetime
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEC = os.path.join(ROOT, "docs", "decisions.md")
ORD = os.path.join(ROOT, "docs", "orders.md")
DEC_ARC = os.path.join(ROOT, "docs", "decisions-archive-2026-11.md")
ORD_ARC = os.path.join(ROOT, "docs", "orders-archive.md")

LIMITS = {DEC: 200 * 1024, ORD: 250 * 1024}
BLOCK_RE = re.compile(r"^##\s.*?(\d{4}-\d{2}-\d{2})")
ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})")


def read_text(path):
    with io.open(path, "r", encoding="utf-8", errors="strict") as f:
        return f.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def oldest_block_date(text):
    dates = [BLOCK_RE.match(ln).group(1) for ln in text.splitlines() if BLOCK_RE.match(ln)]
    return min(dates) if dates else "-"


def oldest_row_date(text):
    dates = [ROW_RE.match(ln).group(1) for ln in text.splitlines() if ROW_RE.match(ln)]
    return min(dates) if dates else "-"


def report():
    rows = []
    bad = 0
    for path, oldfn in ((DEC, oldest_block_date), (ORD, oldest_row_date)):
        if not os.path.exists(path):
            rows.append("%s MISSING" % os.path.basename(path))
            bad += 1
            continue
        text = read_text(path)
        size = len(text.encode("utf-8"))
        limit = LIMITS[path]
        over = size > limit
        rows.append("%s %d B / %d B(%.0f%%) oldest=%s %s" % (
            os.path.basename(path), size, limit, 100.0 * size / limit,
            oldfn(text), "OVER" if over else "ok"))
        if over:
            bad += 1
    print("[ledger-split] " + " | ".join(rows))
    return 1 if bad else 0


def split_blocks(cut, text):
    lines = text.splitlines(keepends=True)
    preamble, blocks, cur = [], [], None
    for ln in lines:
        m = BLOCK_RE.match(ln)
        if m:
            if cur is not None:
                blocks.append(cur)
            cur = {"date": m.group(1), "lines": [ln]}
        elif cur is None:
            preamble.append(ln)
        else:
            cur["lines"].append(ln)
    if cur is not None:
        blocks.append(cur)
    old = [b for b in blocks if b["date"] < cut]
    keep = [b for b in blocks if b["date"] >= cut]
    return "".join(preamble + [l for b in keep for l in b["lines"]]), \
           "".join(l for b in old for l in b["lines"]), len(old), len(keep)


def split_rows(cut, text):
    keep, old = [], []
    for ln in text.splitlines(keepends=True):
        m = ROW_RE.match(ln)
        (old if (m and m.group(1) < cut) else keep).append(ln)
    return "".join(keep), "".join(old), len(old), len(keep)


def apply_split(cut):
    ok = True
    for path, arc, fn, kind in ((DEC, DEC_ARC, split_blocks, "decisions"),
                                (ORD, ORD_ARC, split_rows, "orders")):
        text = read_text(path)
        before = len(text.encode("utf-8"))
        new, moved, n_old, n_keep = fn(cut, text)
        new_b = len(new.encode("utf-8"))
        moved_b = len(moved.encode("utf-8"))
        if new_b + moved_b != before:
            raise SystemExit("[ledger-split] %s 字节不守恒 %d+%d!=%d 已中止" %
                             (kind, new_b, moved_b, before))
        if not moved:
            print("[ledger-split] %s no-op（无早于 %s 的块/行）" % (kind, cut))
            continue
        shutil.copy2(path, path + ".bak-prediv")
        a = read_text(arc) if os.path.exists(arc) else ""
        if a and not a.endswith("\n"):
            a += "\n"
        header = "\n<!-- 分卷归档 %s · 迁入 %d %s · 工具 Tools/ledger_split.py -->\n" % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), n_old,
            "块" if kind == "decisions" else "行")
        write_text(arc, a + header + moved)
        write_text(path, new)
        after = os.path.getsize(path)
        print("[ledger-split] %s moved=%d kept=%d %d B -> %d B (arc=%d)" %
              (kind, n_old, n_keep, before, after, os.path.getsize(arc)))
        ok = ok and after < LIMITS[path]
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--cut", default="")
    a = ap.parse_args()
    if a.apply:
        cut = a.cut or "-"
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", cut):
            raise SystemExit("[ledger-split] --apply 必须带 --cut YYYY-MM-DD")
        rc = apply_split(cut)
        report()
        return rc
    return report()


if __name__ == "__main__":
    sys.exit(main())
