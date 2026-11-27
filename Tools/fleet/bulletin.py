#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机队互报：每台机每天发一张简报，主控合成一块板——消除信息孤岛。

CEO 2026-11-04：机队信息和产出要及时互相同步，不要形成信息孤岛。

为什么不能只靠 git 收据（现状的三个孤岛）：
  1. 回执只说"我跑完了"，不说"我产出了什么、在哪个路径、多大、sha 多少"
     → 别的机器不知道能不能用、要不要去取
  2. 大件（成片/LoRA/素材）在 media/，被 gitignore，任何机器都看不到对方有什么
  3. 阻塞信息只在本地 lanes/*.json 里，别人不知道"我在等你的某件产物"

本工具只做确定性的事：
  --post      ：本机扫自己近 N 小时的新产物，写 BULLETIN-<node>-<date>.json（进 git，很小）
  --aggregate ：读全队简报 → SYNC-BOARD.md（一屏：谁产了什么、谁卡在哪、谁等谁）+ ISLANDS.json

孤岛判据（机器可判）：他人简报里登记、而本机路径不存在且我从未见过的产物条目数。
  注意：这不是"错误"，是"传输通道缺失"的度量；数值长期不降才说明通道该修了。
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SYN = os.path.join(FLEET, "sync")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
WINDOW_H = 26
KEEP = 200            # 每台机保留最近 N 条产物登记
EXTS = (".mp4", ".mov", ".png", ".jpg", ".wav", ".mp3", ".json", ".csv", ".md", ".safetensors", ".zip", ".apk")


def sha256(p, cap=64 * 1024 * 1024):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
            if n >= cap:
                break
    return h.hexdigest()


def recent_outputs(hours):
    cutoff = time.time() - hours * 3600
    out = []
    for base in ("cph4/fleet/queue-receipts", "cph4/fleet/lib", "media"):
        d = os.path.join(ROOT, base)
        if not os.path.isdir(d):
            continue
        for dp, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x not in ("_legacy", "_trash", "__pycache__")]
            for n in files:
                if not n.lower().endswith(EXTS):
                    continue
                p = os.path.join(dp, n)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if st.st_mtime < cutoff:
                    continue
                # 噪声过滤（2026-11-04 实测）：_last_lane/_preflight 这类运行痕迹、
                # 以及 <1KB 的空回执不是"产出"，登进简报只会把真产物淹掉
                if n.startswith("_") or (st.st_size < 1024 and not n.lower().endswith((".mp4", ".png", ".jpg", ".wav"))):
                    continue
                out.append({"path": os.path.relpath(p, ROOT), "bytes": st.st_size,
                            "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),
                            "sha": sha256(p)})
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out[:KEEP]


def post(node, hours):
    os.makedirs(SYN, exist_ok=True)
    day = time.strftime("%Y%m%d")
    lane = {}
    try:
        lane = json.load(open(os.path.join(FLEET, "lanes", "%s.json" % node), encoding="utf-8"))
    except Exception:
        pass
    blocked = []
    try:
        jobs = json.load(open(os.path.join(FLEET, "dispatcher", "MASTER-STATE.json"), encoding="utf-8"))
        me = (jobs.get("lanes") or {}).get(node) or {}
        if me.get("idle_reason"):
            blocked.append({"what": "idle", "why": str(me["idle_reason"])[:120]})
    except Exception:
        pass
    for n in os.listdir(RECEIPTS) if os.path.isdir(RECEIPTS) else []:
        if not n.endswith(".json") or node not in n:
            continue
        p = os.path.join(RECEIPTS, n)
        if time.time() - os.path.getmtime(p) > hours * 3600:
            continue
        try:
            r = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if r.get("rc") not in (0, "0") and not r.get("receipt_is_not_deliverable"):
            blocked.append({"what": str(r.get("id") or n)[:60],
                            "why": "%s %s" % (r.get("error_class") or "rc=%s" % r.get("rc"),
                                              (r.get("stdout_tail") or "")[:80])})
    # 受阻按 error_class 去重，只留最近 6 条：同一类失败说一次就够
    uniq, seen_cls = [], set()
    for b in blocked:
        cls = (b.get("why") or "")[:24]
        if cls in seen_cls:
            continue
        seen_cls.add(cls)
        uniq.append(b)
    blocked = uniq[:6]
    rec = {"node": node, "date": day, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "window_h": hours, "produced": recent_outputs(hours),
           "blocked": blocked[:12],
           "job": (lane.get("job") or None)}
    p = os.path.join(SYN, "BULLETIN-%s-%s.json" % (node, day))
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("bulletin %s: produced=%d blocked=%d -> %s" % (node, len(rec["produced"]), len(blocked),
                                                         os.path.relpath(p, ROOT)))


def aggregate():
    if not os.path.isdir(SYN):
        print("没有简报目录")
        return
    cards = {}
    for n in sorted(os.listdir(SYN)):
        if n.startswith("BULLETIN-") and n.endswith(".json"):
            try:
                c = json.load(open(os.path.join(SYN, n), encoding="utf-8"))
            except Exception:
                continue
            node = c.get("node")
            if node not in cards or str(c.get("ts")) > str(cards[node].get("ts")):
                cards[node] = c
    island = []
    rows = []
    for node, c in cards.items():
        for a in c.get("produced") or []:
            here = os.path.exists(os.path.join(ROOT, a["path"]))
            if not here:
                island.append({"from": node, "path": a["path"], "bytes": a["bytes"]})
        rows.append(c)
    # 名册与新鲜度（2026-11-04）：只报"收到几份"会掩盖"四台机只有一台在报"。
    # 名册取 lanes/ 下真实存在的机器文件；每台给最近一份简报的年龄。
    roster = []
    lanes_dir = os.path.join(FLEET, "lanes")
    if os.path.isdir(lanes_dir):
        roster = [f[:-5] for f in os.listdir(lanes_dir) if f.endswith(".json")]
    fresh, stale = {}, []
    for n in roster:
        c = cards.get(n)
        if not c:
            fresh[n] = None
            stale.append(n)
            continue
        try:
            t = datetime.strptime(str(c.get("ts"))[:19], "%Y-%m-%dT%H:%M:%S")
            fresh[n] = round((datetime.now() - t).total_seconds() / 3600, 1)
        except Exception:
            fresh[n] = None
            stale.append(n)

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "nodes": len(cards),
           "roster": sorted(set(roster)), "missing_nodes": stale,
           "age_h": fresh, "islands": len(island), "island_sample": island[:10]}
    json.dump(rec, open(os.path.join(FLEET, "ISLANDS.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = ["# 机队互报（%s）" % rec["ts"], "",
          "上报 %d / 名册 %d 台；本机看不到的他人产物 %d 件（传输通道度量，不是错误）"
          % (len(cards), len(rec["roster"]), len(island)), ""]
    if rec["missing_nodes"]:
        md.append("**未上报**：%s —— 这些机的产出主控看不见，不能当成「全队同步」"
                  % "、".join(rec["missing_nodes"]))
        md.append("")
    for n in rec["roster"]:
        age = rec["age_h"].get(n)
        md.append("- %s：%s" % (n, ("无简报" if age is None else "最近一份 %.1fh 前" % age)))
    md.append("")
    for node, c in sorted(cards.items()):
        md.append("## %s（%s，窗口 %sh）" % (node, c.get("date"), c.get("window_h")))
        md.append("- 产出 %d 件" % len(c.get("produced") or []))
        for a in (c.get("produced") or [])[:6]:
            md.append("  - `%s`（%dKB, %s…）" % (a["path"], a["bytes"] // 1024, (a["sha"] or "")[:10]))
        if c.get("blocked"):
            md.append("- 受阻 %d 条" % len(c["blocked"]))
            for b in c["blocked"][:4]:
                md.append("  - %s：%s" % (b.get("what"), b.get("why")))
        md.append("")
    open(os.path.join(FLEET, "SYNC-BOARD.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("board: nodes=%d islands=%d -> cph4/fleet/SYNC-BOARD.md" % (len(cards), len(island)))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--node", default="")
    ap.add_argument("--hours", type=int, default=WINDOW_H)
    a = ap.parse_args(argv)
    node = a.node or os.uname().nodename.split(".")[0] if hasattr(os, "uname") else a.node
    if a.post:
        post(node, a.hours)
    if a.aggregate or not a.post:
        aggregate()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))