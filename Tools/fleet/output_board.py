#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""output_board.py - 产出看板：把"完成了多少卡"换成"盘上到底有什么东西"。

为什么（2026-11-09 CEO「规则和工作流很健全，但看不到什么产出」）：
  队列只证明"卡在流转"，不证明"东西被做出来"。本件只认磁盘事实：
  卡上写的 deliverable 是否存在、多大、什么时候改的；并按"产品件/内部件"分开算。
  内部件（审计/核对/回执/canary）再多也不等于产出，必须和产品件分开看。

用法：
  python3 Tools/fleet/output_board.py [--days 7] [--json out]
产出：cph4/fleet/OUTPUT-BOARD.md
"""
import argparse
import collections
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
OUT = os.path.join(F, "OUTPUT-BOARD.md")

PRODUCT_PREFIX = ("gaming/", "media/", "quant/", "domain/", "life/", "compute/", "house/", "research/")
INFRA_HINT = ("audits/", "state/", "queue-receipts/", "canary/", "dispatcher/", "lanes/", "rehearsal/")


def load():
    rows = []
    for line in open(QUEUE, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def kind(path):
    p = path.replace(os.sep, "/")
    if any(h in p for h in INFRA_HINT):
        return "infra"
    if p.startswith(PRODUCT_PREFIX) or "/outbound/" in p or "/deliverables/" in p:
        return "product"
    return "other"


def stat(path):
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    try:
        s = os.stat(p)
        return s.st_size, s.st_mtime
    except OSError:
        return None, None


PRODUCT_DIRS = ("media", "gaming", "domain", "life", "quant", "compute", "house", "research")
SKIP = {".git", "node_modules", "__pycache__", ".venv", "state"}


def loose_files(days, limit=25):
    """不依赖卡的产品文件：盘上真实成品，按 mtime 取最近的。"""
    cut = time.time() - days * 86400
    out = []
    for d in PRODUCT_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dp, dn, fn in os.walk(base):
            dn[:] = [x for x in dn if x not in SKIP and not x.startswith(".")]
            for f in fn:
                if f.startswith("."):
                    continue
                p = os.path.join(dp, f)
                try:
                    s = os.stat(p)
                except OSError:
                    continue
                if s.st_size < 50 * 1024 or s.st_mtime < cut:
                    continue
                out.append((s.st_mtime, s.st_size, os.path.relpath(p, ROOT)))
    return sorted(out, reverse=True)[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json", default=os.path.join(F, "state", "output-board.json"))
    a = ap.parse_args()

    now = time.time()
    rows = load()
    done = [r for r in rows if r.get("state") == "DONE"]
    recent = [r for r in done if (stat(r.get("deliverable") or "")[1] or 0) > now - a.days * 86400]

    buckets = collections.Counter()
    by_line = collections.Counter()
    product_files, infra_files, missing = [], [], []
    for r in done:
        d = (r.get("deliverable") or "").strip()
        if not d:
            continue
        size, mtime = stat(d)
        k = kind(d)
        buckets[k] += 1
        by_line[(r.get("line") or "?", k)] += 1
        if size is None:
            missing.append((r.get("id"), d))
        elif k == "product":
            product_files.append((mtime, size, d, r.get("line")))
        else:
            infra_files.append((mtime, size, d, r.get("line")))

    running = [r for r in rows if r.get("state") in ("OPEN", "RUNNING", "CLAIMED")]

    lines = ["# 产出看板（盘上事实）", ""]
    lines.append("> 判据：只认卡上 deliverable 在盘上存在；产品件与内部件分开算。")
    lines.append("> 生成时间：%s；近 %d 天口径。" % (time.strftime("%Y-%m-%d %H:%M"), a.days))
    lines.append("")
    lines.append("## 一、总数")
    lines.append("")
    lines.append("| 口径 | 数量 |")
    lines.append("|---|---|")
    lines.append("| DONE 卡 | %d |" % len(done))
    lines.append("| 交付物存在 | %d |" % (len(product_files) + len(infra_files)))
    lines.append("| **产品件** | **%d** |" % len(product_files))
    lines.append("| 内部件（审计/回执/状态） | %d |" % len(infra_files))
    lines.append("| 交付物缺失 | %d |" % len(missing))
    lines.append("| 近 %d 天更新的产品件 | %d |" % (a.days, len([x for x in product_files if x[0] > now - a.days * 86400])))
    lines.append("| 在跑卡 | %d |" % len(running))
    lines.append("")

    lines.append("## 二、近 %d 天产品件（按时间）" % a.days)
    lines.append("")
    recent_p = [x for x in product_files if x[0] > now - a.days * 86400]
    if recent_p:
        for mtime, size, d, line in sorted(recent_p, reverse=True)[:25]:
            lines.append("- %s · %.1f KB · %s · %s" % (time.strftime("%m-%d %H:%M", time.localtime(mtime)),
                                                       size / 1024, line or "?", d))
    else:
        lines.append("- （无）")
    lines.append("")

    lines.append("## 三、按线：产品件 / 内部件")
    lines.append("")
    lines.append("| 线 | 产品件 | 内部件 |")
    lines.append("|---|---|---|")
    for ln in sorted({k[0] for k in by_line}):
        lines.append("| %s | %d | %d |" % (ln, by_line.get((ln, "product"), 0), by_line.get((ln, "infra"), 0)))
    lines.append("")

    lines.append("## 四、在跑的卡")
    lines.append("")
    for r in running[:10]:
        lines.append("- %s · %s · %s · %s" % (r.get("state"), r.get("line") or "?",
                                              r.get("id"), r.get("owner") or "-"))
    if not running:
        lines.append("- （无）")
    lines.append("")

    loose = loose_files(a.days)
    lines.append("## 五、盘上成品（不依赖卡，近 %d 天，>50KB）" % a.days)
    lines.append("")
    if loose:
        for mtime, size, d in loose:
            lines.append("- %s · %.1f MB · %s" % (time.strftime("%m-%d %H:%M", time.localtime(mtime)),
                                                  size / 1048576.0, d))
    else:
        lines.append("- （无）")
    lines.append("")

    if missing:
        lines.append("## 六、声称 DONE 但盘上没有（%d）" % len(missing))
        lines.append("")
        for i, d in missing[:15]:
            lines.append("- %s → %s" % (i, d))
        lines.append("")

    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "done": len(done),
               "product": len(product_files), "infra": len(infra_files),
               "missing": len(missing), "running": len(running)},
              open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("board: %s | product=%d infra=%d missing=%d running=%d" %
          (OUT, len(product_files), len(infra_files), len(missing), len(running)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
