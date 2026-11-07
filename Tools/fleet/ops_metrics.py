# -*- coding: utf-8 -*-
"""ops_metrics.py - 三块缺失维度的度量：允许失败率(SLO)、产物质量(rubric)、成本归因。

为什么要有它：此前只有二元绿。偶发失败会误触发停线，系统性劣化却每轮都"绿"。
外部调研（LangChain/StackAI/Google SRE）一致的三条：
  1. 故障常藏在 HTTP 200 背后 -> 要质量分，不只看 rc；
  2. 成本是一等信号 -> 要知道钱花在哪条线；
  3. 用错误预算而不是零容忍 -> 才知道"还能坏几次"。

全部由盘上事实计算，模型不参与算数。
Usage: ops_metrics.py [--json]
"""
import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
PULSE = os.path.join(FLEET, "dispatcher", "PULSE.json")
SPEND = os.path.join(FLEET, "token-ledger", "SPEND.jsonl")
SVC = os.path.join(FLEET, "SERVICE-LEVEL-v1.json")
OUT = os.path.join(FLEET, "OPS-METRICS.md")
STATE_OUT = os.path.join(STATE, "ops-metrics.json")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def rows(p):
    out = []
    try:
        with open(p, encoding="utf-8") as f:
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


def age_days(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 86400.0
    except Exception:
        return None


# ---- 1. SLO / 错误预算 ---------------------------------------------------------
def slo_metrics(cfg):
    win = float(cfg.get("window_days") or 7) * 86400
    q = rows(QUEUE)
    # dispatch: 有 owner 的卡里 DONE 且交付物可判
    owned = [r for r in q if str(r.get("owner") or "").strip()]
    done_ok = 0
    for r in owned:
        if str(r.get("state", "")).upper() != "DONE":
            continue
        d = str(r.get("deliverable") or "").strip()
        if not d or re.match(r"^([A-Za-z]:[\\/]|\\\\|/)", d):
            done_ok += 1        # 远端产物本机不可判，按成交计
            continue
        if d.startswith(("quant/", "gaming/", "media/", "life/", "compute/", "domain/",
                         "house/", "cph4/fleet/state/")):
            done_ok += 1
            continue
        if os.path.exists(os.path.join(ROOT, d)):
            done_ok += 1
    dispatch = (done_ok / len(owned)) if owned else None

    # execution: 回执 rc=0 占比
    recs = []
    if os.path.isdir(RECEIPTS):
        for f in os.listdir(RECEIPTS):
            p = os.path.join(RECEIPTS, f)
            if not f.endswith(".json") or f.startswith("self-improve-"):
                continue
            a = age_days(p)
            if a is not None and a * 86400 > win:
                continue
            d = jload(p)
            if isinstance(d, dict) and "rc" in d:
                recs.append(d)
    exe = (sum(1 for d in recs if int(d.get("rc") or 0) == 0) / len(recs)) if recs else None

    # pulse / sync: 读最近轮次与日志
    pj = jload(PULSE, {}) or {}
    pulse_ok = None
    st = pj.get("stages") or {}
    if isinstance(st, dict) and st:
        bad = 0
        for v in st.values():
            if isinstance(v, dict) and v.get("rc") not in (0, None):
                bad += 1
        pulse_ok = 1.0 - bad / len(st)
    sync_ok = None
    try:
        lines = [ln for ln in open("/tmp/fluxgroup-pulse.log", encoding="utf-8", errors="replace")
                 if "pulse " in ln and "git=" in ln]
        tail = lines[-360:]
        if tail:
            good = sum(1 for ln in tail if "git=ok" in ln and "push=ok" in ln)
            sync_ok = good / len(tail)
    except Exception:
        pass

    # demand: 机检通过率
    dv = jload(os.path.join(STATE, "demand-audit.json"), {}) or {}
    c = dv.get("counts") or {}
    ok, gap = c.get("OK", 0), c.get("GAP", 0)
    demand = (ok / (ok + gap)) if (ok + gap) else None

    got = {"dispatch": (dispatch, "%d/%d 张有主卡成交" % (done_ok, len(owned))),
           "execution": (exe, "%d 份回执" % len(recs)),
           "pulse": (pulse_ok, "%d 个阶段" % len(st)),
           "sync": (sync_ok, "%d 轮样本" % (len(lines[-360:]) if sync_ok is not None else 0)),
           "demand": (demand, "%d 通过 / %d 缺口" % (ok, gap))}
    out = []
    for s in cfg.get("services") or []:
        v, ev = got.get(s["id"], (None, "无数据"))
        slo = float(s.get("slo") or 0)
        budget = None
        burn = None
        if v is not None:
            # 错误预算余额 = 允许失败率 - 实际失败率（百分点）
            budget = round((1 - slo) - (1 - v), 4)
            burn = round((1 - v) / (1 - slo), 2) if slo < 1 else None
        out.append({"id": s["id"], "name": s["name"], "sli": v, "slo": slo,
                    "budget_left": budget, "burn": burn, "evidence": ev})
    return out


# ---- 2. 产物质量 rubric --------------------------------------------------------
def quality(cfg, limit=40):
    rubric = (cfg.get("quality_rubric") or {}).get("items") or []
    q = [r for r in rows(QUEUE) if str(r.get("state", "")).upper() == "DONE"][-limit:]
    scored, low = [], []
    for r in q:
        score = 0
        d = str(r.get("deliverable") or "").strip()
        if d and r.get("accept") and (r.get("cmd") or r.get("prompt")):
            score += 1                      # 字段齐
        if r.get("cmd") or r.get("prompt"):
            score += 1                      # 可复现
        rid = str(r.get("id") or "")
        rec = None
        for f in (os.path.join(RECEIPTS, "%s-%s.json" % (rid, r.get("owner") or "")),
                  os.path.join(RECEIPTS, "%s.json" % rid)):
            if os.path.exists(f):
                rec = jload(f)
                break
        if isinstance(rec, dict) and "rc" in rec:
            score += 1                      # 有证据
        if d and not re.match(r"^([A-Za-z]:[\\/]|\\\\|/)", d) and \
                not d.startswith(("quant/", "gaming/", "media/", "life/", "compute/",
                                  "domain/", "house/")):
            p = os.path.join(ROOT, d)
            if os.path.exists(p):
                score += 1                  # 新鲜（产物存在）
        scored.append(score)
        if score < 2:
            low.append({"id": rid, "score": score, "deliverable": d[:40]})
    avg = (sum(scored) / len(scored)) if scored else None
    return {"n": len(scored), "avg": round(avg, 2) if avg is not None else None,
            "low": low[:8], "rubric": rubric}


# ---- 3. 成本归因 --------------------------------------------------------------
def cost(cfg):
    per_min = float((cfg.get("cost") or {}).get("local_cny_per_min") or 0.02)
    cloud = 0.0
    by_line = {}
    for r in rows(SPEND):
        c = float(r.get("cny") or r.get("cost_cny") or 0)
        cloud += c
        ln = str(r.get("line") or "未标")
        by_line[ln] = by_line.get(ln, 0) + c
    # 本地机时：用回执 seconds × 单价
    local_min = 0.0
    by_line_local = {}
    if os.path.isdir(RECEIPTS):
        for f in os.listdir(RECEIPTS):
            if not f.endswith(".json"):
                continue
            d = jload(os.path.join(RECEIPTS, f))
            if not isinstance(d, dict):
                continue
            sec = float(d.get("seconds") or 0)
            if sec <= 0:
                continue
            local_min += sec / 60.0
            ln = str(d.get("line") or "未标")
            by_line_local[ln] = by_line_local.get(ln, 0) + sec / 60.0 * per_min
    top = sorted(by_line_local.items(), key=lambda x: -x[1])[:5]
    return {"cloud_cny": round(cloud, 2), "local_min": round(local_min, 1),
            "local_cny": round(local_min * per_min, 2), "top_lines_local": top,
            "per_min": per_min}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    cfg = jload(SVC) or {}
    slo = slo_metrics(cfg)
    qual = quality(cfg)
    cst = cost(cfg)

    hot = [s for s in slo if s["burn"] is not None and s["burn"] >= 1.0]
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = ["# 运营度量 %s" % now, "",
         "_三块此前没有的维度：允许失败率、产物质量、成本归因。数字全部由盘上事实算。_", ""]
    L.append("## 一、还能坏几次（错误预算）")
    L.append("")
    L.append("| 服务 | SLI | SLO | 预算余额 | 燃尽倍率 | 判定 |")
    L.append("|---|---|---|---|---|---|")
    for s in slo:
        v = "—" if s["sli"] is None else "%.1f%%" % (s["sli"] * 100)
        b = "—" if s["budget_left"] is None else "%+.1f%%" % (s["budget_left"] * 100)
        br = "—" if s["burn"] is None else "%.2fx" % s["burn"]
        verdict = ("无数据" if s["sli"] is None else
                   "🔴 超预算" if (s["burn"] or 0) >= 1 else "🟢 有余额")
        L.append("| %s | %s | %.0f%% | %s | %s | %s |"
                 % (s["name"], v, s["slo"] * 100, b, br, verdict))
    L.append("")
    L.append("## 二、产物质量（rubric 0–4 分）")
    L.append("")
    L.append("最近 %d 张完成卡：平均 **%s 分**；低于 2 分的 %d 张。"
             % (qual["n"], qual["avg"] if qual["avg"] is not None else "—", len(qual["low"])))
    if qual["low"]:
        L.append("")
        for x in qual["low"]:
            L.append("- %s（%d 分）产出：%s" % (x["id"], x["score"], x["deliverable"]))
    L.append("")
    L.append("## 三、成本归因")
    L.append("")
    L.append("- 云端累计：**¥%.2f**｜本地机时：%.1f 分钟 ≈ **¥%.2f**（按 ¥%.2f/分钟）"
             % (cst["cloud_cny"], cst["local_min"], cst["local_cny"], cst["per_min"]))
    if cst["top_lines_local"]:
        L.append("- 本地机时最贵的线：%s"
                 % "；".join("%s ¥%.2f" % (k, v) for k, v in cst["top_lines_local"]))
    L.append("")
    if hot:
        L.append("## 需要处理")
        L.append("")
        for s in hot:
            L.append("- **%s** 燃尽 %.2fx（SLI %.1f%% vs SLO %.0f%%）：%s"
                     % (s["name"], s["burn"], (s["sli"] or 0) * 100, s["slo"] * 100, s["evidence"]))
        L.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(STATE, exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "slo": slo, "quality": qual, "cost": cst},
                  f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": "BUDGET-HOT" if hot else "OK",
                      "slo_tracked": len([s for s in slo if s["sli"] is not None]),
                      "quality_avg": qual["avg"], "cloud_cny": cst["cloud_cny"],
                      "board": os.path.relpath(OUT, ROOT)}, ensure_ascii=False))
    for s in hot:
        print("  HOT", s["id"], "burn=%.2f" % s["burn"], s["evidence"])
    return 1 if hot else 0


if __name__ == "__main__":
    sys.exit(main())