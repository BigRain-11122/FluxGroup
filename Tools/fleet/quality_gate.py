#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_gate.py - 交付验收门：没有过线证据的产物，一律不算交付。

为什么（2026-11-03 CEO「务必有质量验收，不要产出垃圾」）：卡上写 DONE 只说明命令跑完了，
不说明东西能看/能玩/能卖。本工具把 QUALITY-BAR-v1 的标准变成"必须有哪几份闸回执、
且回执必须 PASS"，缺一份就是缺口，不做主观辩护。

每条线的必需闸（可在 cph4/fleet/QUALITY-GATES.json 覆盖）：
  bigstream-mv : 交付闸 / 转场审计 / 稳定性 / 逐镜
  bigstream-duanju / drama : 配音质检 / 带声合流 / 可发集数
  biggame      : 可上线包清单 + 10 秒爽点记录
  bigmoney     : 回测 + 一页结论（四件齐）

用法：
  python3 quality_gate.py --line bigstream-mv [--date 2026-11-03] [--json]
Exit: 0 = 全过；2 = 有缺口（会列出缺哪份、哪份 FAIL）；1 = 配置读不了。
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
CONF = os.path.join(FLEET, "QUALITY-GATES.json")
STATE = os.path.join(FLEET, "state")

DEFAULT_GATES = {
    # 一个闸可能有两个文件名：闸自己的产物（mv-gate-v721-*.json）与车道回执
    # （bigstream-mv-gate-*-bm-a.json）。两种都要认，否则"跑了但判失败"会被报成"缺"。
    "bigstream-mv": [["mv-gate", "bigstream-mv-gate"],
                     ["mv-transition", "bigstream-mv-transition"],
                     ["mv-stability", "bigstream-mv-stability"],
                     ["mv-shot-audit", "bigstream-mv-shot-audit"]],
    "bigstream-duanju": ["duanju-inventory", "duanju-tts-qc", "duanju-remux", "duanju-shippable"],
    "bigstream-drama": ["duanju-inventory", "duanju-tts-qc", "duanju-remux", "duanju-shippable"],
    "biggame": ["game-packs", "game-10s"],
    "bigmoney": ["quant-conclusion"],
}


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def gates_for(line):
    conf = jload(CONF, {}) or {}
    return (conf.get("lines") or {}).get(line) or DEFAULT_GATES.get(line) or []


def latest(prefix, day=None):
    """Find the newest receipt starting with prefix (optionally for a given date)."""
    pats = [os.path.join(RECEIPTS, prefix + "*.json")]
    out = []
    for p in pats:
        for f in glob.glob(p):
            if day and day not in os.path.basename(f):
                continue
            out.append((os.path.getmtime(f), f))
    if not out:
        return None
    out.sort()
    return out[-1][1]


def verdict_of(path):
    """A gate verdict: JSON may carry verdict/status/rc, or be a plain report."""
    d = jload(path, None)
    if not isinstance(d, dict):
        return "UNREADABLE", "不是 JSON"
    if "verdict" in d:
        v = str(d["verdict"]).upper()
        return ("PASS" if v in ("PASS", "OK") else "FAIL"), v
    if "status" in d:
        v = str(d["status"]).upper()
        return ("PASS" if v in ("OK", "PASS", "NO-REPO") else "FAIL"), v
    if "rc" in d:
        rc = d.get("rc")
        return ("PASS" if rc == 0 else "FAIL"), "rc=%s" % rc
    tail = str(d.get("stdout_tail") or "")
    m = re.search(r"VERDICT[:\s]+(PASS|FAIL)", tail)
    if m:
        return m.group(1), "stdout VERDICT"
    if d.get("missing"):
        return "FAIL", "缺件:" + ",".join(map(str, d["missing"]))
    if d.get("deliverable_exists"):
        return "PASS", "产物在盘"
    return "UNKNOWN", "无判据字段"


def check(line, day=None):
    day = day or date.today().isoformat()
    need = gates_for(line)
    rows, gaps = [], []
    for g in need:
        prefixes = g if isinstance(g, list) else [g]
        p = None
        for pre in prefixes:
            p = latest(pre, day) or p
        if not p:
            rows.append({"gate": prefixes[0], "file": None, "state": "MISSING"})
            gaps.append("%s:缺" % prefixes[0])
            continue
        st, why = verdict_of(p)
        rows.append({"gate": prefixes[0], "file": os.path.relpath(p, ROOT), "state": st, "why": why,
                     "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))})
        if st != "PASS":
            gaps.append("%s:%s(%s)" % (prefixes[0], st, why))
    verdict = "PASS" if need and not gaps else ("NO-GATES" if not need else "FAIL")
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "line": line, "day": day,
           "needed": need, "gates": rows, "gaps": gaps, "verdict": verdict,
           "note": "DONE 不等于交付；这里只看闸回执，缺一份就算没交付。"}
    out["status"] = out["verdict"]
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "quality-%s.json" % line), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true", help="跑全部已知线")
    ap.add_argument("--out", default="", help="另存一份到指定路径（给验收卡当交付物）")
    a = ap.parse_args(argv)
    lines = list(DEFAULT_GATES) if (a.all or not a.line) else [a.line]
    outs = [check(l, a.date or None) for l in lines]
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(outs if a.all else outs[0], f, ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(outs if a.all else outs[0], ensure_ascii=False, indent=1))
    else:
        for o in outs:
            print("QUALITY %-18s %s" % (o["line"], o["verdict"]))
            for r in o["gates"]:
                print("   %-16s %-8s %s" % (r["gate"], r["state"], r.get("why") or r.get("mtime") or ""))
            for g in o["gaps"]:
                print("   ! %s" % g)
    return 0 if all(o["verdict"] == "PASS" for o in outs) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))