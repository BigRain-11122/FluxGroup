#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""city_state.py - 城市面清单状态：12 个面现在各自是活的、空的、还是被挡住的。

为什么（2026-11-03 CEO：「你继续梳理硅基城市元宇宙搭建的顶层设计和工作流规则」＋同日长期要求
「以后都是你要考虑的比我全面和科学，不是我说哪里弄哪里」）：
  城市的顶层设计不缺文档，缺的是"每一面现在什么状态、卡在谁手里、什么条件下才会动"。
  面清单落成机读件（cph4/fleet/CITY-FACES-v1.json），由本工具每轮核对盘上证据，
  汇报时先说"扫了 N 面，其中 M 面受阻/空白"，再说被点名的那一项。

判据（每面独立）：
  1. 声明的证据路径在不在盘 → 不在=受阻（本机看不到，就不能对它下结论）
  2. 状态字段本身（在役/空白/受阻/待裁）
  3. 有 trigger 的面必须写清楚触发条件（缺=治理漏洞，不是文案问题）

用法：
  python3 city_state.py [--json] [--out receipts/city-state.json] [--face space]
Exit: 0 全部在役或待裁；1 有受阻/空白（告警，不阻断）；2 面清单读不了。
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "CITY-FACES-v1.json")


def check(face):
    ev_missing = [p for p in (face.get("evidence") or []) if not os.path.exists(os.path.join(ROOT, p))]
    gaps = []
    if ev_missing:
        gaps.append("证据不在本机：%s" % ", ".join(ev_missing))
    if not (face.get("trigger") or "").strip():
        gaps.append("没写触发条件（这条面永远不会被自动提起）")
    status = face.get("status") or "未知"
    if ev_missing and status == "在役":
        # 声称在役却看不到证据 = 假绿，比空白更糟
        status = "受阻"
        gaps.append("状态自称在役但证据不可见 → 降级为受阻")
    return {"id": face.get("id"), "name": face.get("name"), "status": status,
            "owner": face.get("owner"), "claim": face.get("claim"),
            "evidence_missing": ev_missing, "trigger": face.get("trigger"),
            "next": face.get("next"), "gaps": gaps}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--face", default="")
    a = ap.parse_args(argv)
    try:
        spec = json.load(open(SPEC, encoding="utf-8-sig"))
    except Exception as e:
        print("读不到面清单 %s：%s" % (SPEC, e))
        return 2
    faces = [check(f) for f in (spec.get("faces") or [])]
    if a.face:
        faces = [f for f in faces if f["id"] == a.face] or faces
    tally = {}
    for f in faces:
        tally[f["status"]] = tally.get(f["status"], 0) + 1
    blocked = [f for f in faces if f["status"] in ("受阻", "空白")]
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "line": spec.get("line"),
           "faces_total": len(faces), "tally": tally,
           "blocked": [{"id": f["id"], "name": f["name"], "status": f["status"],
                        "next": f["next"]} for f in blocked],
           "faces": faces,
           "verdict": "OK" if not blocked else "GAPS"}
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("城市面清单 %d 面  %s" % (len(faces), " ".join("%s=%d" % kv for kv in sorted(tally.items()))))
        for f in faces:
            mark = {"在役": "  ", "空白": "空", "受阻": "阻", "待裁": "待"}.get(f["status"], "?")
            print(" %s %-14s %-6s %s" % (mark, f["id"], f["status"], f["name"]))
            for g in f["gaps"]:
                print("      ! %s" % g)
        if blocked:
            print("未决（%d）：%s" % (len(blocked), "; ".join("%s→%s" % (b["id"], b["next"]) for b in blocked[:5])))
    return 0 if not blocked else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))