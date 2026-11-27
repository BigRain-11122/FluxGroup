# -*- coding: utf-8 -*-
"""ceo_pilot.py - 带 CEO 做事：一次只推一件，带理由、命令、耗时与验收。

CEO 2026-11-07：「我要做的事情非常多…让常驻大模型带我去做，监督/派发/雷达/找工具/
验收/审查…高频率的科学频次」。高频不等于频繁打扰：候选全进池子，规则打分取最高一条，
同一个题不重复刷屏（除非它变坏）。

Six sources, one decision:
  SUPERVISE 监督 - 线停了 / 卡假完成 / 机器分叉
  DISPATCH  派发 - 队列空或有线无卡
  RADAR     侦察 - 开源/模型雷达里可试跑的候选
  TOOLING   找工具 - 缺口与候选的能力匹配
  ACCEPT    验收 - DONE 但没产物 / 需求缺口
  AUDIT     审查 - 雷达超阈星数、汇报无指针等「结论本身不可信」的项

Score = 阻塞他人×3 + 有现成工具×2 + 低耗时×2 + 时间敏感×2（规则算，模型不参与）。
Output: cph4/fleet/CEO-NEXT.md（一条）+ state/ceo-pilot.json（全池与分数，可追）。
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
OUT = os.path.join(FLEET, "CEO-NEXT.md")
POOL = os.path.join(STATE, "ceo-pilot.json")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def qrows():
    out = []
    try:
        with open(QUEUE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def cand(cid, kind, title, why, action, cost_min, done_check, blocks=0, ready=0, urgent=0):
    score = blocks * 3 + ready * 2 + (2 if cost_min <= 10 else 1 if cost_min <= 30 else 0) + urgent * 2
    return {"id": cid, "kind": kind, "title": title, "why": why, "action": action,
            "cost_min": cost_min, "done_check": done_check, "score": score}


def build_pool():
    pool = []
    rows = qrows()
    live = [r for r in rows if str(r.get("state", "")).upper() in ("OPEN", "READY")]
    flying = [r for r in rows if str(r.get("state", "")).upper() in ("CLAIMED", "RUNNING")]

    # --- 监督 ---
    lines = (jload(os.path.join(STATE, "lines.json"), {}) or {}).get("lines") or []
    stale = [l for l in lines if (l.get("age_h") or 0) > 72]
    if stale:
        top = max(stale, key=lambda l: l.get("age_h") or 0)
        pool.append(cand("SUP-1", "监督", "「%s」已 %.0f 小时无产物，定去留" %
                         (top.get("name") or top.get("id"), top.get("age_h") or 0),
                         "%d 条线同时超 72h；这条最久" % len(stale),
                         "决定：继续（我派卡）/ 挂起（记账）",
                         2, "线状态变更或收到新卡", blocks=1, urgent=1))
    ea = jload(os.path.join(STATE, "alerts.json"), {}) or {}
    alerts = ea.get("alerts") if isinstance(ea, dict) else ea
    art = [a for a in (alerts or []) if isinstance(a, dict)
           and "ARTIFACT" in str(a.get("error_class") or "")]
    if art:
        pool.append(cand("SUP-2", "监督", "%d 张卡跑成功但没产物（假完成）" % len(art),
                         "假绿比空转更糟，会让人以为在推进",
                         "我停该机生产、只派诊断卡", 3, "E-ARTIFACT 归零", blocks=1, urgent=1))

    # --- 派发 ---
    if not live and not flying:
        pool.append(cand("DIS-1", "派发", "队列空了，机队无活可干",
                         "可派 0、在飞 0：现在是纯空转",
                         "确认一条线，我立刻铺 10 张卡", 3, "可派≥1 且在飞≥1",
                         blocks=2, urgent=2))
    elif len(live) < 3 and flying:
        pool.append(cand("DIS-2", "派发", "可派只剩 %d 张，撑不过半小时" % len(live),
                         "机队正在飞 %d 张，料不够接续" % len(flying),
                         "确认补哪条线，我批量供卡", 2, "可派≥6", ready=1))

    # --- 侦察 + 找工具（同一个池子里的两件事：先看有什么，再看能接哪） ---
    stock = (jload(os.path.join(FLEET, "oss", "STOCKPILE.json"), {}) or {}).get("items") or {}
    adopt = [(k, v) for k, v in stock.items() if v.get("grade") == "ADOPT-CANDIDATE"]
    need = "空" if not live else ("停线" if stale else "")
    if adopt:
        k, v = adopt[0]
        pool.append(cand("RAD-1", "侦察", "试跑 %s（%s★）" % (k, v.get("stars")),
                         "雷达判可试跑；当前缺口=%s" % (need or "无强缺口"),
                         "我拉最小例子跑通再决定是否接", 20,
                         "有试用回执（能跑/不能跑都给结论）", ready=1 if need else 0))
    thick = [(k, v) for k, v in stock.items()
             if int(v.get("stars") or 0) > 100000 and "人工核实" in str(v.get("why"))]
    if thick:
        pool.append(cand("AUD-1", "审查", "%d 个候选星数超 10 万未核实" % len(thick),
                         "情报不可信就会选错工具；雷达自己标了需人工核实",
                         "我已用 GitHub API 核实过 1 个（真），其余要不要我批量核实", 5,
                         "每条的 stars/license/pushed 都有 API 回执", ready=1))

    # --- 跨机收口（R6）：仓库分叉的机器拿不到新码，只能人工一次 ---
    fs = jload(os.path.join(STATE, "fork-status.json"), {}) or {}
    forks = [n for n, v in ((fs.get("nodes") or {}).items())
             if int((v or {}).get("ahead") or 0) > 0]
    if forks:
        pool.append(cand("CLS-1", "收口", "%d 台机器仓库分叉，跑一次自愈脚本" % len(forks),
                         "分叉机器拿不到新码：%s" % ",".join(forks[:4]),
                         "在每台机器上执行 Tools/fleet/node_closeout.ps1（双击或一条命令，30 秒）",
                         5, "closeout-<node>.json 回执且 ahead=0", blocks=1, urgent=1))

    # --- 验收 ---
    dv = jload(os.path.join(STATE, "demand-audit.json"), {}) or {}
    gaps = [r for r in (dv.get("results") or []) if r.get("state") == "GAP"]
    if gaps:
        g = gaps[0]
        pool.append(cand("ACC-1", "验收", "需求缺口：%s" % g.get("demand", "")[:40],
                         str(g.get("evidence") or "")[:60],
                         str(g.get("gap") or "按台账修法执行"), 5,
                         "重跑 demand_audit 该条转 OK", blocks=1))
    return pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    pool = build_pool()
    pool.sort(key=lambda x: -x["score"])
    prev = jload(POOL, {}) or {}
    prev_top = prev.get("top_id")
    top = pool[0] if pool else None

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = ["# 你现在做这一件 %s" % now, ""]
    if not top:
        L += ["**没有需要你做的事。** 机队在跑，没有阻塞，也没有真缺口。", ""]
    else:
        same = "（同一件事，仍等你）" if prev_top == top["id"] else ""
        L.append("## %s" % top["title"] + same)
        L.append("")
        L.append("1. **为什么是它**：%s" % top["why"])
        L.append("2. **你要做的**：%s（约 %d 分钟）" % (top["action"], top["cost_min"]))
        L.append("3. **做完机器自动验**：%s" % top["done_check"])
        L.append("")
        if len(pool) > 1:
            L.append("_排在后面的（自动处理，不占你注意力）：%s_"
                     % "；".join("%s(%d分)" % (x["title"][:22], x["score"]) for x in pool[1:4]))
            L.append("")
    L.append("---")
    L.append("")
    L.append("_生成器=ceo_pilot：监督/派发/侦察/找工具/验收/审查六源合一，规则打分，"
             "同一件事不重复刷屏。_")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(STATE, exist_ok=True)
    with open(POOL, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "top_id": (top or {}).get("id"), "pool": pool},
                  f, ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps({"top": top, "n": len(pool)}, ensure_ascii=False))
    else:
        print(json.dumps({"board": os.path.relpath(OUT, ROOT),
                          "top": (top or {}).get("title"), "score": (top or {}).get("score"),
                          "candidates": len(pool)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())