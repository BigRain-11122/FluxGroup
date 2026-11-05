#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""unlock.py - 解锁预案执行器：你办好一件事，系统自动接上后面的事。

为什么（CEO 2026-11-05「我办好了证件，他们接下来要做什么？这道理很难吗」）：
  之前的状态是：卡在你的物理件上 → 那条线就"停着"，等你回来再问"下一步干什么"。
  正确做法是把"办好之后做什么"提前写死成预案，系统每轮自己检测触发条件，
  一触发就把后续活直接派下去，不需要任何人再解释一遍。

触发三类（都可机器判定）：
  path_exists     某个文件/目录出现（如 docs/legal/MERCHANT-ID.md）
  node_online     某台机心跳出现（如 bm-d 入网）
  order_keyword   令台账出现关键词（如"放行游戏截图"）

产出：
  state/unlocks.json   当前：哪些还在等、哪些已解锁、解锁后派了什么
  plans/UNLOCK-<date>.md 人读一页

用法：python3 Tools/fleet/unlock.py [--json] [--dry]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "state", "unlocks.json")
MD = os.path.join(F, "plans", "UNLOCK-%s.md" % time.strftime("%Y%m%d"))


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def triggered(t):
    typ = t.get("type")
    if typ == "path_exists":
        p = t.get("path") or ""
        return os.path.exists(p if os.path.isabs(p) else os.path.join(ROOT, p))
    if typ == "node_online":
        ms = jload(os.path.join(F, "dispatcher", "MASTER-STATE.json"), {}) or {}
        v = (ms.get("lanes") or {}).get(t.get("node")) or {}
        return bool(v.get("online")) and (v.get("hb_age_s") is not None)
    if typ == "order_keyword":
        kw = t.get("keyword") or ""
        try:
            return kw and kw in open(os.path.join(ROOT, "docs", "orders.md"),
                                     encoding="utf-8", errors="ignore").read()
        except Exception:
            return False
    return False


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    spec = jload(os.path.join(F, "UNLOCK-PLANS.json"), {}) or {}
    queue = rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    backlog = rows(os.path.join(F, "PRODUCTION-BACKLOG.jsonl"))
    have = {r.get("id") for r in queue + backlog}
    today = time.strftime("%Y%m%d")

    waiting, unlocked, created, need_build = [], [], [], []
    prework_done, prework_new = [], []
    for plan in spec.get("plans") or []:
        # 前置件（不依赖物理件）：现在就派，不等触发。
        # CEO 2026-11-05：「虽然物理件卡住了，后续工作可以提前开展而不是等待」。
        for pw in (plan.get("prework") or []):
            wid = "PW-%s-%s" % (plan.get("id", "X").replace("U-", ""),
                                abs(hash(pw.get("step"))) % 1000)
            if wid in have:
                prework_done.append(wid)
                continue
            if not pw.get("cmd"):
                need_build.append({"plan": plan.get("id"), "step": pw.get("step"),
                                   "build": pw.get("needs_build") or "缺可执行命令",
                                   "deliverable": pw.get("deliverable")})
                continue
            dl = str(pw.get("deliverable") or "").replace("{date}", today)
            if dl and os.path.exists(os.path.join(ROOT, dl)):
                prework_done.append(wid)          # 产物已在盘 = 前置件已完成
                continue
            prework_new.append({"id": wid, "title": "[前置] " + str(pw.get("step")),
                                "cmd": pw["cmd"].replace("{date}", today), "cwd": "",
                                "needs": pw.get("needs") or "cpu", "minutes": 3,
                                "deliverable": dl, "accept": pw.get("accept") or "",
                                "nodes": [pw.get("owner") or "bm-m"], "prio": "P1",
                                "line": plan.get("line"), "state": "OPEN",
                                "created_by": "unlock:prework",
                                "created_at": datetime.now().isoformat(timespec="seconds")})
        ok = triggered(plan.get("trigger") or {})
        rec = {"id": plan.get("id"), "line": plan.get("line"),
               "waiting_on": plan.get("waiting_on"), "triggered": ok}
        if not ok:
            waiting.append(rec)
            continue
        steps = []
        for st in plan.get("on_unlock") or []:
            cid = "UNL-%s-%s" % (plan.get("id", "X").replace("U-", ""), today)
            steps.append(st.get("step"))
            if st.get("needs_build") and not st.get("cmd"):
                # 需要先建工具：不造"没有命令的卡"，改为提一条 L2 决策（诚实）
                need_build.append({"plan": plan.get("id"), "step": st.get("step"),
                                   "build": st.get("needs_build"),
                                   "deliverable": st.get("deliverable")})
                continue
            if not st.get("cmd"):
                continue
            card_id = "%s-%s" % (cid, abs(hash(st.get("step"))) % 1000)
            if card_id in have:
                continue
            cmd = st["cmd"].replace("{date}", today)
            dl = str(st.get("deliverable") or "").replace("{date}", today)
            card = {"id": card_id, "title": st.get("step"), "cmd": cmd, "cwd": "",
                    "needs": st.get("needs") or "cpu", "minutes": 15,
                    "deliverable": dl, "accept": st.get("accept") or "",
                    "nodes": [st.get("owner") or "bm-a"], "prio": "P0",
                    "line": plan.get("line"), "state": "OPEN",
                    "created_by": "unlock", "created_at": datetime.now().isoformat(timespec="seconds")}
            created.append(card)
        rec["steps"] = steps
        unlocked.append(rec)

    for c in prework_new:
        if c["id"] not in have:
            created.append(c)
    if created and not a.dry:
        try:
            import fleet_lane as fl
            fl.merge_jsonl(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), created)
        except Exception as e:
            print("[unlock] merge failed: %s" % str(e)[:80])

    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "waiting": waiting, "unlocked": unlocked,
           "created": [c["id"] for c in created], "need_build": need_build,
           "prework_ready": prework_done,
           "note": "已解锁但缺工具的步骤不造卡，转 L2 决策：先建工具再派"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    lines = ["# 解锁预案 %s" % out["ts"], "", "## 还在等你（办好后自动解锁）", ""]
    for w in waiting:
        lines.append("- **%s**（%s）：%s" % (w["line"], w["id"], w["waiting_on"]))
    if not waiting:
        lines.append("- 无")
    lines += ["", "## 已解锁并派活", ""]
    for u in unlocked:
        lines.append("- %s：%s" % (u["line"], " / ".join(u.get("steps") or [])))
    if not unlocked:
        lines.append("- 无")
    if need_build:
        lines += ["", "## 解锁后要先建工具（不造假卡）", ""]
        for b in need_build:
            lines.append("- %s：%s —— %s" % (b["plan"], b["step"], b["build"]))
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[unlock] waiting=%d unlocked=%d created=%d need-build=%d prework-done=%d"
              % (len(waiting), len(unlocked), len(created), len(need_build), len(prework_done)))
        for w in waiting:
            print("  等：%s ← %s" % (w["line"], w["waiting_on"]))
        for c in out["created"]:
            print("  + %s" % c)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))