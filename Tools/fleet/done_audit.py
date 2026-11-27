#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""done_audit.py - 已结案的卡必须真有交付物，否则降级为 UNVERIFIED。

为什么（2026-11-04 主控职责面 mc-self）：
  "回执≠产出"已经写进 closer，但历史账还带着一批 DONE：实测 244 张带交付物的 DONE 卡里
  8 张本机路径不存在。其中 5 张的 parent 目录根本不在本机（quant/ 子仓），那不是假绿而是
  主控看不见；真正可判死的是「仓内相对路径 + 文件不在」。两类必须分开，否则一边造假账、
  一边冤枉别的机器。

判据（每条都可复核）：
  OK              路径在盘
  CROSS-HOST      绝对路径/盘符/外盘——本机无法核验，不改状态
  SUBREPO-ABSENT  parent 顶层目录不在本机（子仓/独立仓）——不改状态
  MISSING         仓内相对路径且文件不在 → 降级 UNVERIFIED 并写原因
  BAD-FIELD       deliverable 不是路径（写成了一句话）
Exit: 0 无真缺失；2 有真缺失（已降级，账与盘对齐前不许报绿）
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
OUT = os.path.join(FLEET, "state", "done-audit.json")
MD = os.path.join(FLEET, "DONE-AUDIT.md")


def classify(d):
    s = str(d or "").strip()
    if not s:
        return "BAD-FIELD"
    if ":" in s and not s.startswith("./") or s.startswith("/Volumes") or s.startswith("/"):
        return "CROSS-HOST"
    if not ("/" in s or "\\" in s or "." in os.path.basename(s)):
        return "BAD-FIELD"
    p = s.replace("\\", "/")
    if os.path.exists(os.path.join(ROOT, p)):
        return "OK"
    head = p.split("/")[0]
    if head and not os.path.exists(os.path.join(ROOT, head)):
        return "SUBREPO-ABSENT"
    # 被 .gitignore 排除的目录=独立仓/本机不落地的产物（如 quant/bigmoney、media/），
    # 主控本来就看不见，判 MISSING 会冤枉别的机器（实测 5 条 quant 结果属此类）。
    try:
        r = subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", p],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return "SUBREPO-ABSENT"
    except Exception:
        pass
    return "MISSING"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--apply", action="store_true", help="把 MISSING 降级为 UNVERIFIED")
    a = ap.parse_args(argv)

    buckets = {"OK": 0, "CROSS-HOST": 0, "SUBREPO-ABSENT": 0, "MISSING": 0, "BAD-FIELD": 0}
    miss, patch_q, patch_b = [], [], []
    for path, rows, patch in ((QUEUE, fl.read_jsonl(QUEUE) if os.path.exists(QUEUE) else [], patch_q),
                              (BACKLOG, fl.read_jsonl(BACKLOG) if os.path.exists(BACKLOG) else [],
                               patch_b)):
        for r in rows:
            if str(r.get("state")).upper() != "DONE":
                continue
            if not r.get("deliverable"):
                continue
            k = classify(r.get("deliverable"))
            buckets[k] = buckets.get(k, 0) + 1
            if k == "MISSING":
                miss.append({"id": r.get("id"), "line": r.get("line"),
                             "deliverable": r.get("deliverable"), "owner": r.get("owner")})
                if a.apply:
                    nr = dict(r)
                    nr["state"] = "UNVERIFIED"
                    nr["unverified_reason"] = "交付物不在盘（done_audit 2026-11-04）"
                    nr["verified_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
                    patch.append(nr)

    if a.apply and patch_q:
        fl.merge_jsonl(QUEUE, patch_q)
    if a.apply and patch_b:
        fl.merge_jsonl(BACKLOG, patch_b)

    state = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
             "buckets": buckets, "missing": miss, "downgraded": len(patch_q) + len(patch_b) if a.apply else 0}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lines = ["# DONE 卡交付物审计（%s）" % state["ts"][:16], "",
             "OK %d · 跨机不可核验 %d · 子仓不可见 %d · **真缺失 %d** · 字段写成一句话 %d"
             % (buckets["OK"], buckets["CROSS-HOST"], buckets["SUBREPO-ABSENT"],
                buckets["MISSING"], buckets["BAD-FIELD"]), ""]
    for m in miss:
        lines.append("- [降级 UNVERIFIED] %s（%s）交付物 %s 不在盘"
                     % (m["id"], m["line"], m["deliverable"]))
    open(MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        print("[done-audit] OK=%d cross=%d subrepo=%d missing=%d bad-field=%d%s"
              % (buckets["OK"], buckets["CROSS-HOST"], buckets["SUBREPO-ABSENT"],
                 buckets["MISSING"], buckets["BAD-FIELD"], " (applied)" if a.apply else ""))
        for m in miss:
            print("  [missing] %-40s %s" % (m["id"], m["deliverable"][:50]))
    return 2 if buckets["MISSING"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))