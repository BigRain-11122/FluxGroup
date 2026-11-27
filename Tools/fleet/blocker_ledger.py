#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blocker_ledger.py - 堵点台账：把"卡住的东西"全部列出来，每条给打通方式。

为什么（CEO 2026-11-05「把堵点卡点全部科学的打通，等物理件不是理由」）：
  卡点散在六个地方（队列、备队列、线路、机器、预算、解锁预案），没人合起来看。
  合成一张账之后，每条都必须有 owner + 打通动作 + 判定，**不允许出现"等"**。

分类与打通原则：
  B-CAP     产能不足（机器/槽位）      → 换机、开槽、夜窗、云端兜底
  B-INPUT   缺输入（文件/素材）        → 找替代输入、降级产物、先做不依赖它的部分
  B-SKILL   缺工具/能力                → 建最小工具或改派有能力的机
  B-BUG     卡反复失败/账本冲突        → 定位根因、修码或改派
  B-PHYS    物理件（钱/证件/现场）      → **不阻塞**：前置件先做 + 触发即解锁 + 其余线照跑
  B-DECIDE  需要人定（方向/红线）       → 走分层决策，到期兜底
  B-GATE    闸红                        → 进 L1/L2，修到归零

产出：state/blockers.json + BLOCKERS.md（按能不能自动打通排序）
用法：python3 Tools/fleet/blocker_ledger.py [--json]
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "state", "blockers.json")
MD = os.path.join(F, "BLOCKERS.md")


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


def _rc_to_class(rc, outcome):
    if rc is None:
        return "E-NO-RECEIPT"
    rc = int(rc) if str(rc).lstrip("-").isdigit() else -1
    if rc == 127:
        return "E-CMD-MISSING"
    if rc == 124:
        return "E-TIMEOUT"
    if rc == 126:
        return "E-ENV"
    if rc == 2:
        return "E-INPUT"
    if rc == 3:
        return "E-BLOCKED-INPUT"
    if rc == 0:
        return "E-CONTRACT"
    return "E-UNKNOWN"


def fix_all():
    """把可自动打通的堵点真打掉。三件：
       F1 失败卡无根因 → 按回执 rc 反推 error_class（无回执判 E-NO-RECEIPT）
       F2 困在单机的 CPU 卡 → 允许跨机回落（同能力机可接手）
       F3 闸红噪音 → 交给 flux_check 的活跃态作用域（在那边改），这里只统计
    """
    import glob
    import fleet_lane as fl
    fixed_cls, cross, notes = 0, 0, []
    qp = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
    bp = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
    q = rows(qp)
    b = rows(bp)

    # 收执索引：<card>-<node>.json
    rec = {}
    for p in glob.glob(os.path.join(F, "queue-receipts", "*.json")):
        try:
            d = json.load(open(p, encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        cid = d.get("id")
        if cid and cid not in rec:
            rec[cid] = d

    touch_q, touch_b = [], []
    for r in q + b:
        if r.get("state") != "FAILED" or r.get("error_class"):
            continue
        d = rec.get(r.get("id"))
        cls = _rc_to_class((d or {}).get("rc"), (d or {}).get("outcome"))
        r["error_class"] = cls
        r["note"] = (str(r.get("note") or "") + " | auto-classified from receipt").strip(" |")
        fixed_cls += 1
        (touch_q if r in q else touch_b).append(r)

    # F2：bm-m 单槽 + 卡钉在 bm-m 且是纯 CPU → 允许 bm-a 接手
    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    slots = (cfg.get("supply") or {}).get("slots_per_node") or {}
    if int(slots.get("bm-m", 1)) <= 1:
        for r in q + b:
            if r.get("state") not in ("OPEN", "READY"):
                continue
            nodes = list(r.get("nodes") or [])
            if nodes == ["bm-m"] and r.get("needs") == "cpu"                     and int(r.get("minutes") or 0) <= 5 and "bm-a" not in nodes:
                r["nodes"] = nodes + ["bm-a"]
                r["note"] = (str(r.get("note") or "") + " | cross-node: bm-a may take it").strip(" |")
                cross += 1
                (touch_q if r in q else touch_b).append(r)

    if touch_q:
        fl.merge_jsonl(qp, touch_q)
    if touch_b:
        fl.merge_jsonl(bp, touch_b)
    notes.append("F1 补根因 %d 张；F2 跨机回落 %d 张" % (fixed_cls, cross))
    return {"error_class_fixed": fixed_cls, "cross_node": cross, "notes": notes}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fix", action="store_true", help="自动打通可修的堵点（F1/F2）")
    a = ap.parse_args(argv)

    fixed = None
    if a.fix:
        fixed = fix_all()

    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    cap = cfg.get("capacity") or {}
    q = rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    b = rows(os.path.join(F, "PRODUCTION-BACKLOG.jsonl"))
    truth = {l.get("id"): l for l in ((jload(os.path.join(F, "state", "lines.json"), {}) or {})
                                      .get("lines") or [])}
    ms = jload(os.path.join(F, "dispatcher", "MASTER-STATE.json"), {}) or {}
    lanes = ms.get("lanes") or {}
    unlock = jload(os.path.join(F, "state", "unlocks.json"), {}) or {}
    gate = jload(os.path.join(F, "state", "gate-report.json"), {}) or {}
    lb = jload(os.path.join(F, "state", "load-watch.json"), {}) or {}

    items = []

    # 1) 卡住不动的卡（OPEN 但没派出去）
    openc = [r for r in q if r.get("state") == "OPEN"]
    if openc:
        nodes = {}
        for r in openc:
            for n in (r.get("nodes") or ["?"]):
                nodes[n] = nodes.get(n, 0) + 1
        items.append({"id": "B-DISPATCH", "kind": "B-CAP",
                      "what": "OPEN 卡未派出：%s" % ", ".join("%s×%d" % (k, v) for k, v in nodes.items()),
                      "count": len(openc),
                      "unblock": "检查该机车道是否在跑；槽位不足则开槽或跨机回落",
                      "owner": "S2 调度", "auto": True})

    # 2) 反复失败且无根因的卡
    failed = [r for r in q + b if r.get("state") == "FAILED"]
    blind = [r for r in failed if not r.get("error_class")]
    if blind:
        items.append({"id": "B-FAILBLIND", "kind": "B-BUG",
                      "what": "%d 张卡失败但没有 error_class" % len(blind),
                      "count": len(blind),
                      "unblock": "按回执 rc 反推错误类别；无回执的判 E-NO-RECEIPT",
                      "owner": "S3 验收", "auto": True})

    # 3) 断料的活线
    declared = set(((jload(os.path.join(F, "LINE-NEXT-STEPS.json"), {}) or {}).get("lines") or {}).keys())
    busy = {str(r.get("line")) for r in q + b if r.get("state") in ("OPEN", "READY", "RUNNING")}
    blocked = cap.get("blocked_active") or {}
    dry = [l for l, t in truth.items()
           if str(t.get("declared")) == "ACTIVE" and l not in busy and l not in declared and l not in blocked]
    if dry:
        items.append({"id": "B-SUPPLYDRY", "kind": "B-INPUT",
                      "what": "活线断料：%s" % ",".join(dry), "count": len(dry),
                      "unblock": "从工序表/BUSINESS-MAP next_product 生成下一张卡；无可用输入则标具名缺口",
                      "owner": "S2 调度", "auto": True})

    # 4) 物理件（不阻塞，但要看得住前置件是否都做完了）
    for line, why in blocked.items():
        plan = next((p for p in (jload(os.path.join(F, "UNLOCK-PLANS.json"), {}) or {}).get("plans") or []
                     if p.get("line") == line), None)
        pre = len((plan or {}).get("prework") or [])
        items.append({"id": "B-PHYS-%s" % line, "kind": "B-PHYS",
                      "what": "%s：%s" % (line, why), "count": 1,
                      "unblock": "前置件先做（已配 %d 项）+ 触发即解锁；其余线照跑" % pre,
                      "owner": "CEO（物理件）/ S2（前置件）", "auto": pre > 0})

    # 5) 闸红
    inv = (gate.get("invariants") or {})
    if (inv.get("red") or []):
        items.append({"id": "B-GATE", "kind": "B-GATE",
                      "what": "不变量红 %d 项：%s" % (len(inv["red"]),
                                                 ",".join("%s×%s" % (i, c) for i, c in inv["red"][:6])),
                      "count": len(inv["red"]),
                      "unblock": "已进 L2 决策，按项修到归零（修卡/修闸/改判据三选一）",
                      "owner": "S4 账房", "auto": True})

    # 6) 产能缺口（机器在线但没吃满 / 槽位与库存不匹配）
    gaps = lb.get("gaps") or []
    partial = [g for g in gaps if g.get("kind") in ("UNDER-DISPATCH", "SUPPLY-DRY", "PARTIAL")]
    if partial:
        items.append({"id": "B-LOAD", "kind": "B-CAP",
                      "what": "满负荷缺口 %d 处：%s" % (len(partial),
                                                  "; ".join(g.get("why", "")[:40] for g in partial[:3])),
                      "count": len(partial),
                      "unblock": "补料/开槽/换机；主控只吃轻活",
                      "owner": "S2 调度", "auto": True})

    # 7) 单一 GPU 风险（结构性堵点）
    gpu_nodes = [n for n, v in lanes.items() if v.get("online")]
    items.append({"id": "B-GPUSINGLE", "kind": "B-CAP",
                  "what": "GPU 产能集中在单机（bm-c），该机排队即全线等待", "count": 1,
                  "unblock": "夜窗开放 bm-a 的 4070S 备援；重活按云端兜底（有预算闸）",
                  "owner": "S2 调度", "auto": True})

    # 8) 未入网节点
    offline = [n for n in ("bm-a", "bm-b", "bm-c", "bm-d") if not (lanes.get(n) or {}).get("online")]
    if offline:
        items.append({"id": "B-NODEOFF", "kind": "B-PHYS",
                      "what": "节点不在线：%s" % ",".join(offline), "count": len(offline),
                      "unblock": "bm-d 需现场装机（物理件）；其余查心跳/调度任务",
                      "owner": "CEO（bm-d）/ S7 自愈", "auto": False})

    items.sort(key=lambda x: (not x["auto"], x["kind"]))
    auto_n = len([i for i in items if i["auto"]])
    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "total": len(items), "auto_unblockable": auto_n,
           "items": items, "fixed": fixed,
           "rule": "每条堵点必须有 owner + 打通动作；'等'不是动作"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    lines = ["# 堵点台账 %s" % out["ts"], "",
             "共 %d 条，其中 %d 条可自动打通。" % (out["total"], auto_n), "",
             "| 类型 | 堵点 | 打通方式 | 责任 | 自动 |", "|---|---|---|---|---|"]
    for i in items:
        lines.append("| %s | %s | %s | %s | %s |" % (
            i["kind"], i["what"][:60], i["unblock"][:70], i["owner"],
            "是" if i["auto"] else "否"))
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[blockers] total=%d auto=%d" % (out["total"], auto_n))
        for i in items:
            print("  %-9s %-52s → %s" % (i["kind"], i["what"][:52], i["unblock"][:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))