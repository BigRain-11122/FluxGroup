#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""face_report.py — 读 TRAINING-FACES-v1.json，把"还没解决的面"打出来（一屏，可机读）。

为什么要有这个：CEO 2026-11-21「当然你科学全面的推进」+ 领域整面律——
一份面清单只在回复里讲一次，下一轮就没人记得还剩哪些没做。落成机读件 + 每次
训练前跑一遍，未决项才会自己冒出来，而不是靠人回忆。

退出码：0=全 ok（或只有 running）/ 1=有 gap 或 unknown（未达标，不是故障）

用法：
  python3 Tools/fleet/face_report.py            # 一屏
  python3 Tools/fleet/face_report.py --json     # 机读
  python3 Tools/fleet/face_report.py --only-gap # 只列未决
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FACES = os.path.join(ROOT, "cph4", "fleet", "social", "TRAINING-FACES-v1.json")

BAD = ("gap", "unknown")


def load(path=None):
    d = json.load(open(path or FACES, encoding="utf-8"))
    fs = d.get("faces") or []
    if not fs:
        raise SystemExit("面清单为空：%s" % (path or FACES))
    return d, fs


def summarize(fs):
    from collections import Counter
    return dict(Counter((f.get("status") or "unknown") for f in fs))


def self_test():
    """负控：缺 status 必须算 unknown（不许静默当 ok）；--only-gap 必须能滤掉 ok。"""
    fs = [{"id": "A", "status": "ok"}, {"id": "B"}, {"id": "C", "status": "gap"}]
    s = summarize(fs)
    ok1 = s.get("unknown") == 1 and s.get("ok") == 1 and s.get("gap") == 1
    gaps = [f for f in fs if (f.get("status") or "unknown") in BAD]
    ok2 = len(gaps) == 2 and all(f["id"] != "A" for f in gaps)
    ok = ok1 and ok2
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "缺 status 算 unknown": ok1,
                      "只列未决": ok2}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only-gap", action="store_true")
    ap.add_argument("--path", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    d, fs = load(a.path or None)
    s = summarize(fs)
    gaps = [f for f in fs if (f.get("status") or "unknown") in BAD]
    if a.json:
        print(json.dumps({"version": d.get("version"), "counts": s,
                          "gaps": [{"id": f.get("id"), "name": f.get("name"),
                                    "status": f.get("status"), "gap": f.get("gap"),
                                    "action": f.get("action"), "trigger": f.get("trigger")}
                                   for f in gaps]}, ensure_ascii=False, indent=1))
    else:
        print("== 训练面（%s）：ok %d / running %d / gap %d / unknown %d =="
              % (d.get("version"), s.get("ok", 0), s.get("running", 0),
                 s.get("gap", 0), s.get("unknown", 0)))
        if not a.only_gap:
            for f in fs:
                mark = {"ok": "✅", "running": "⏳"}.get(f.get("status"), "❗")
                print("%s %-4s %-18s %s" % (mark, f.get("id"), f.get("name"),
                                            (f.get("now") or "")[:60]))
        if gaps:
            print("\n未决 %d 项：" % len(gaps))
            for f in gaps:
                print("  %s %s｜缺：%s｜下一步：%s" % (f.get("id"), f.get("name"),
                                                    (f.get("gap") or "-")[:60],
                                                    (f.get("action") or "-")[:60]))
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
