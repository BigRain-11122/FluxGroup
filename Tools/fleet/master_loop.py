#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master_loop.py - 主控的决策大脑（规则版·2026-11-05）。

为什么要它：机队有 69 个观察员，各写各的报告，没有一个东西做决定。这一站只做决定，
并把结论压成 CEO 能一眼核对的样子：

  四线四行 —— 每条 P0 线一行：最后真实产出 / 今天推进 / 卡点类型 / 本轮唯一动作

判定只用规则与盘上事实（CEO 2026-11-05 选型：规则大脑），不调模型、不编理由。
每条决定都写进 state/master-decision.json，可回溯"为什么派了这张卡"。

输入（全部来自盘上）：
  state/lines.json         真值（census 产出，已排除记账目录）
  PRODUCTION-QUEUE.jsonl    队列现状
  BUSINESS-MAP-v1.json      卡点类型与目标
  AUTONOMY-CONFIG.json      优先级线与阈值
  state/squeeze.json        各机余量

输出：
  cph4/fleet/MASTER-SCREEN.md          四线四行（CEO 面）
  cph4/fleet/state/master-decision.json 决策日志

用法：python3 Tools/fleet/master_loop.py [--root PATH] [--json]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def rows_of(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out


def today():
    return datetime.now().strftime("%Y-%m-%d")


def infer_line(card):
    """卡片归属：优先 line 字段；缺失时按 id 关键词归属，绝不瞎猜成别的线。"""
    ln = card.get("line")
    if ln:
        return str(ln)
    cid = str(card.get("id") or "").upper()
    for key, line in (("MV", "bigstream-mv"), ("DRAMA", "bigstream-drama"),
                      ("DUANJU", "bigstream-duanju"), ("BIGGAME", "biggame"),
                      ("GIM", "biggame"), ("ASSET", "asset-lib"),
                      ("VCORP", "asset-lib"), ("QUANT", "bigmoney"),
                      ("BIGMONEY", "bigmoney"), ("CAR", "car-gaming"),
                      ("FLUXVERSE", "fluxverse"), ("CITY", "fluxverse")):
        if key in cid:
            return line
    return "UNKNOWN"


def line_row(line_id, cfg, lines_truth, queue, biz, squeeze):
    """一条线一行：真实产出 / 今日推进 / 卡点 / 唯一动作。规则顺序即优先级。"""
    truth = (lines_truth or {}).get(line_id) or {}
    obs = truth.get("observed") or "-"
    age = truth.get("age_h")
    out_txt = ("无真实产出（%s）" % obs) if age is None else ("%.1fh 前" % age)

    cards = [c for c in queue if infer_line(c) == line_id]
    done_today = [c for c in cards if c.get("state") == "DONE"
                  and str(c.get("closed_at") or "")[:10] == today()]
    running = [c for c in cards if c.get("state") == "RUNNING"]
    openc = [c for c in cards if c.get("state") == "OPEN"]
    blocked = [c for c in cards if c.get("state") == "FAILED"
               and str(c.get("error_class") or "") == "E-ROOTCAUSE-3X"]

    stall_s = int(((cfg.get("progress") or {}).get("stall_after_s")) or 1800)
    now = datetime.now()
    stalled = []
    for c in running:
        try:
            idle = (now - datetime.fromisoformat(str(c.get("progress_ts")))).total_seconds()
        except Exception:
            idle = None
        if idle is not None and idle > stall_s:
            stalled.append(c.get("id"))

    b = (biz or {}).get(line_id) or {}
    blocker_type = (b.get("blocker_type") or "").upper()

    idle_nodes = [n.get("node") for n in (squeeze.get("nodes") or [])
                  if int(n.get("can_take_more") or 0) > 0]

    # ---- 规则大脑：一条线只给一个动作 ----
    if blocked:
        action, why = "STOP-DIAGNOSE", "%d 张卡已停线待根因：%s" % (len(blocked), blocked[0].get("id"))
        btype = "ENGINE"
    elif stalled:
        action, why = "RELEASE", "RUNNING 卡 %d 分钟无进展：%s" % (stall_s // 60, stalled[0])
        btype = "ENGINE"
    elif openc:
        action, why = "DISPATCH", "队列里有 %d 张可派卡，等待机器认领" % len(openc)
        btype = "ENGINE"
    elif blocker_type == "CEO":
        action, why = "ASK-CEO", b.get("blocker") or "需要 CEO 的物理件或决定"
        btype = "CEO"
    elif blocker_type == "EXTERNAL":
        action, why = "WAIT-EXTERNAL", b.get("blocker") or "等外部回复"
        btype = "EXTERNAL"
    elif age is not None and age > 24:
        action, why = "SUPPLY", "真实产出已 %.0fh，队列无卡：需要补下一张卡" % age
        btype = blocker_type or "ENGINE"
    else:
        action, why = "HOLD", "有产出、无积压：保持现状"
        btype = blocker_type or "-"

    return {
        "line": line_id,
        "name": (b.get("name") or line_id),
        "prio": (b.get("prio") or "-"),
        "real_output": out_txt,
        "age_h": age,
        "done_today": len(done_today),
        "running": [c.get("id") for c in running],
        "open": len(openc),
        "blocker_type": btype,
        "action": action,
        "why": why,
        "idle_nodes": idle_nodes,
    }


def render_screen(rows, decision, ts):
    lines = ["# 主控一屏 %s" % ts, "",
             "**现在最重要的一件事**：%s" % decision["top"], "",
             "| 线 | 最后真实产出 | 今天完成 | 卡点 | 本轮动作 |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %d 张 | %s | %s |" % (
            r["name"], r["real_output"], r["done_today"], r["blocker_type"], r["action"]))
    lines += ["", "## 每条线的理由（可核）", ""]
    for r in rows:
        lines.append("- **%s**：%s" % (r["name"], r["why"]))
    if decision.get("ceo_items"):
        lines += ["", "## 需要你决定的（其余已自决）", ""]
        for i, it in enumerate(decision["ceo_items"], 1):
            lines.append("%d. %s" % (i, it))
    lines += ["", "_规则：ENGINE=机队自解 / CEO=物理件 / INPUT=缺投料 / EXTERNAL=等外部。_"]
    return "\n".join(lines) + "\n"


def act(rows, root, cfg):
    """把"该做的动作"真的做掉，并记录做了什么。

    分工：这一站只触发既有的腿，不自己生产——
      缺卡 → night_plan（按 LINE-NEXT-STEPS 声明补卡）
      可派 → workgen --node <有空槽的机>（把 READY 推进队列，交给 master 分配）
    释放/停线由 closer 负责（同轮已在跑），这里不重复。
    """
    import subprocess
    did = []
    idle = sorted({n for r in rows for n in r.get("idle_nodes") or []})
    need_supply = any(r["action"] == "SUPPLY" for r in rows)
    need_dispatch = any(r["action"] == "DISPATCH" for r in rows)
    need_release = any(r["action"] == "RELEASE" for r in rows)

    def run(args, tag):
        try:
            p = subprocess.run([sys.executable] + args, cwd=root, capture_output=True,
                               text=True, timeout=180)
            tail = (p.stdout or p.stderr or "").strip().splitlines()
            did.append({"tag": tag, "rc": p.returncode, "tail": tail[-1] if tail else ""})
        except Exception as e:
            did.append({"tag": tag, "rc": -1, "tail": str(e)[:120]})

    if need_release:
        # 卡死先收回：closer 负责 STALL 释放与 3 次停线，这里只是把它拉起来。
        run([os.path.join(root, "Tools", "fleet", "closer.py")], "closer")
    if need_supply:
        run([os.path.join(root, "Tools", "fleet", "night_plan.py")], "night_plan")
    if need_dispatch:
        for n in idle[:3]:
            run([os.path.join(root, "Tools", "fleet", "workgen.py"), "--root", root,
                 "--node", n], "workgen:%s" % n)
    return did


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--act", action="store_true", help="真的执行动作（补卡/推卡），不只是报告")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    f = os.path.join(root, "cph4", "fleet")

    cfg = jload(os.path.join(f, "AUTONOMY-CONFIG.json"), {}) or {}
    truth = (jload(os.path.join(f, "state", "lines.json"), {}) or {}).get("lines") or []
    truth_by_id = {t.get("id"): t for t in truth}
    queue = rows_of(os.path.join(f, "PRODUCTION-QUEUE.jsonl"))
    biz = {b.get("id"): b for b in
           ((jload(os.path.join(f, "BUSINESS-MAP-v1.json"), {}) or {}).get("businesses") or [])}
    squeeze = jload(os.path.join(f, "state", "squeeze.json"), {}) or {}

    prio_lines = cfg.get("priority_lines") or list(biz)[:4]
    rows = [line_row(l, cfg, truth_by_id, queue, biz, squeeze) for l in prio_lines]

    did = []
    if a.act:
        did = act(rows, root, cfg)
        # 动作做完再看一遍事实：补进去的卡/释放的卡应该反映在下一屏
        queue = rows_of(os.path.join(f, "PRODUCTION-QUEUE.jsonl"))
        truth = (jload(os.path.join(f, "state", "lines.json"), {}) or {}).get("lines") or truth
        truth_by_id = {t.get("id"): t for t in truth}
        rows = [line_row(l, cfg, truth_by_id, queue, biz, squeeze) for l in prio_lines]

    # 顶部那一条：先把会停摆的、再没东西产出的，按优先级取第一条
    order = {"STOP-DIAGNOSE": 0, "RELEASE": 1, "SUPPLY": 2, "DISPATCH": 3,
             "ASK-CEO": 4, "WAIT-EXTERNAL": 5, "HOLD": 6}
    worst = sorted(rows, key=lambda r: (order.get(r["action"], 9), str(r["prio"])))[0]
    top = "%s：%s（%s）" % (worst["name"], worst["action"], worst["why"])

    ceo_items = ["%s：%s" % (r["name"], r["why"]) for r in rows if r["action"] == "ASK-CEO"]
    decision = {"ts": datetime.now().isoformat(timespec="seconds"),
                "policy": "rules-only", "top": top,
                "actions": [{k: r[k] for k in ("line", "action", "why", "blocker_type")}
                            for r in rows],
                "did": did,
                "ceo_items": ceo_items}
    os.makedirs(os.path.join(f, "state"), exist_ok=True)
    with open(os.path.join(f, "state", "master-decision.json"), "w", encoding="utf-8") as fh:
        json.dump(decision, fh, ensure_ascii=False, indent=1)
    screen = render_screen(rows, decision, decision["ts"])
    with open(os.path.join(f, "MASTER-SCREEN.md"), "w", encoding="utf-8") as fh:
        fh.write(screen)
    if a.json:
        print(json.dumps({"decision": decision, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        print(screen)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))