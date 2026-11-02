#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""showcase.py - 作品墙：一页看全部成品，给 CEO 抽查用。

为什么：产物散在 outbound / queue-receipts / ship / 各处目录，CEO 抽查要先找文件。
这里只列"能看/能玩"的东西，并标明它现在处于哪一步：
  待发布 / 已发布（等数据）/ 已发布有数据 / 只有版本没有发布
另外列"半成品"，让你一眼看到哪些是半拉的。

只读。写 cph4/fleet/SHOWCASE.md 并打印。
用法：python3 showcase.py [--json]
"""
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SHIP = os.path.join(FLEET, "ship")
OUT = os.path.join(FLEET, "mv0001-handover", "outbound")
GAME = os.path.join(ROOT, "gaming")


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def ships():
    out = []
    if os.path.isdir(SHIP):
        for n in sorted(os.listdir(SHIP)):
            if n.endswith(".json"):
                o = jload(os.path.join(SHIP, n), {}) or {}
                out.append(o)
    return out


def masters():
    """成片：优先认 outbound 下的 mp4，按名字取版本号。"""
    rows = []
    if os.path.isdir(OUT):
        for dirpath, dirs, files in os.walk(OUT):
            dirs[:] = [d for d in dirs if not d.startswith("_")]
            for f in files:
                if f.endswith(".mp4") and os.path.getsize(os.path.join(dirpath, f)) > 5 * 1024 * 1024:
                    p = os.path.join(dirpath, f)
                    rows.append({"file": os.path.relpath(p, ROOT),
                                 "mb": round(os.path.getsize(p) / 1048576.0, 1),
                                 "mtime": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m-%d %H:%M")})
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return rows


def builds():
    rows = []
    if os.path.isdir(GAME):
        for dirpath, dirs, files in os.walk(GAME):
            dirs[:] = [d for d in dirs if d not in (".git", "Library", "Temp", "obj", "node_modules")]
            for f in files:
                if f.endswith((".apk", ".exe", ".html")) and os.path.getsize(os.path.join(dirpath, f)) > 200 * 1024:
                    p = os.path.join(dirpath, f)
                    rows.append({"file": os.path.relpath(p, ROOT),
                                 "mb": round(os.path.getsize(p) / 1048576.0, 1),
                                 "mtime": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m-%d %H:%M")})
    return rows[:10]


def main(argv):
    s = ships()
    m = masters()
    b = builds()
    published = {x.get("work"): x for x in s}
    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "published": s, "masters": m, "builds": b}

    lines = ["# 作品墙（%s）" % out["ts"][:16], "",
             "> 只列能看/能玩的东西。抽查就点这里。", "",
             "## 一、已发布", ""]
    if s:
        lines += ["| 作品 | 当前版 | 平台 | 发布 | 24h 播放 | 24h 完播 |", "|---|---|---|---|---|---|"]
        for x in s:
            d = (x.get("data") or {}).get("24h") or {}
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                x.get("work"), x.get("current_version"), x.get("platform"),
                (x.get("published_at") or "")[:16], d.get("views", "-"), d.get("finish", "-")))
    else:
        lines.append("（还没有任何发布）")
    lines += ["", "## 二、成片（未发布或待发布）", ""]
    if m:
        lines += ["| 文件 | 大小 | 时间 | 状态 |", "|---|---|---|---|"]
        for x in m[:12]:
            st = "已发布" if any(p in x["file"] for p in published) else "待发布"
            lines.append("| %s | %sMB | %s | %s |" % (x["file"], x["mb"], x["mtime"], st))
    else:
        lines.append("（本机没有成片文件；下面按队列记录列远端成片）")
    # 远端成片：本机看不见，但队列/回执里有记录（2026-11-02：抽查不能只信本机磁盘）
    far = []
    try:
        for l in open(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"), encoding="utf-8"):
            l = l.strip()
            if not l:
                continue
            r = json.loads(l)
            d = str(r.get("deliverable") or "")
            if d.endswith(".mp4") and r.get("state") == "DONE":
                far.append((r.get("id"), d, r.get("owner") or ",".join(r.get("nodes") or []) or "?"))
    except FileNotFoundError:
        pass
    if far:
        lines += ["", "### 远端成片（在别的机器上，本机未同步）", "",
                  "| 卡 | 文件 | 机器 |", "|---|---|---|"]
        for x in far[-10:]:
            lines.append("| %s | %s | %s |" % x)
    lines += ["", "## 三、游戏可玩包", ""]
    if b:
        lines += ["| 文件 | 大小 | 时间 |", "|---|---|---|"]
        for x in b:
            lines.append("| %s | %sMB | %s |" % (x["file"], x["mb"], x["mtime"]))
    else:
        lines.append("（没有可玩包 —— 这是游戏组当前最大的缺口）")

    md = "\n".join(lines) + "\n"
    with open(os.path.join(FLEET, "SHOWCASE.md"), "w", encoding="utf-8") as f:
        f.write(md)
    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))