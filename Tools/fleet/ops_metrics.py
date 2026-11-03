#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ops_metrics.py - 把"做得好不好"变成每天能看的数，而不是感觉。

口径（2026-11-02 定，对应全链条俯瞰的七处断点）：
  一次过闸率  第一次跑就通过、且没重试的卡 / 已收口卡
  返工次数    重试>=1 的卡数 + 售后重开数
  产出年龄    该线证据目录最近一次变动距今小时数（来自 census 投影）
  成本        本机累计执行秒数 × 每机每小时单价（默认 0.6 元/小时，可配置）
  复用率      本线产物引用的输入里，有资产登记的比例（无资产库时留空，不编数）
  自动停线    连续 3 次不过线 / 7 天零产出 → 把线标 PAUSED（可逆，报一屏）

只读输入，写 state/metrics.json；停线写 LINE-REGISTRY.json（带 reason，可人工恢复）。
用法：python3 ops_metrics.py [--json] [--no-autostop]
"""
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
REGISTRY = os.path.join(FLEET, "LINE-REGISTRY.json")
# 自动停线=冷却窗口，不是死刑（2026-11-03）：停线会连带停掉出卡供给，指标冻结后
# 没有恢复路径。24h 后自动回线，仍不达标会再次冷却——反复冷却本身就是需要人判的信号。
AUTOSTOP_COOLDOWN_H = 24
COST = os.path.join(FLEET, "COST-RATES.json")

DEFAULT_RATE = 0.6  # 元 / 机器小时，仅本地电费与折旧的粗算，云端另记


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def jlines(p):
    out = []
    try:
        for l in open(p, encoding="utf-8-sig"):
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def receipts():
    out = {}
    if not os.path.isdir(RECEIPTS):
        return out
    for n in os.listdir(RECEIPTS):
        if not n.endswith(".json"):
            continue
        d = jload(os.path.join(RECEIPTS, n))
        if isinstance(d, dict) and d.get("id"):
            out.setdefault(d["id"], []).append(d)
    return out


def main(argv):
    os.makedirs(STATE, exist_ok=True)
    reg = jload(REGISTRY, {}) or {}
    lines = reg.get("lines") or []
    queue = jlines(QUEUE)
    rec = receipts()
    census = jload(os.path.join(STATE, "lines.json"), {}) or {}
    age_by_line = {r.get("id"): r.get("age_h") for r in (census.get("lines") or [])}
    rate = (jload(COST, {}) or {}).get("cny_per_hour", DEFAULT_RATE)

    # 卡 -> 线：优先用卡里的 line，其次用 id 前缀推断
    def line_of(c):
        if c.get("line"):
            return c["line"]
        i = c.get("id") or ""
        if i.startswith(("R-TTS", "C-VB", "R-VB")):
            return "bigstream-duanju"
        if i.startswith(("R-MV", "C-MV")):
            return "bigstream-mv"
        if "DRAMA" in i or "drama" in i:
            return "bigstream-drama"
        if "RECON" in i:
            return "recon"
        if i.startswith(("C-FIN", "Q-QUANT")):
            return "bigmoney"
        return "unknown"

    per = defaultdict(lambda: {"cards": 0, "done": 0, "failed": 0, "first_pass": 0,
                               "rework": 0, "seconds": 0.0, "last_receipt_h": None,
                               "blocked": 0})
    for c in queue:
        lid = line_of(c)
        m = per[lid]
        m["cards"] += 1
        st = c.get("state")
        retries = int(c.get("retries") or 0)
        secs = 0.0
        for r in rec.get(c.get("id"), []):
            try:
                secs = max(secs, float(r.get("seconds") or 0))
            except (TypeError, ValueError):
                pass
        m["seconds"] += secs
        if st == "DONE":
            m["done"] += 1
            if retries == 0:
                m["first_pass"] += 1
        elif st in ("FAILED", "UNVERIFIED"):
            m["failed"] += 1
            # 缺输入/缺环境不是质量失败（2026-11-03 实锚）：asset-lib 因为有卡落在没有
            # ComfyUI 或没有素材的机器上被判"过闸率<50%"，于是 P0 线被自动停下，而
            # 停下后出卡方不再供卡、指标永远回不来——自我锁死的线。这类卡单独计数。
            if str(c.get("error_class") or "") in ("E-BLOCKED-INPUT", "E-INPUT",
                                                   "E-PATH", "E-MODEL"):
                m["blocked"] += 1
        if retries > 0:
            m["rework"] += 1

    # 还债计划（2026-11-02 自审第 13 条）：baseline 记了多少条债，每周必须降一成。
    # 债不清就会永久合法化，红变成背景色。
    debt_path = os.path.join(STATE, "debt.jsonl")
    debt = None
    try:
        debt = len((jload(os.path.join(FLEET, "INVARIANTS-BASELINE.json"), {}) or {}).get("keys") or [])
        today = datetime.now().strftime("%Y-%m-%d")
        hist = []
        if os.path.exists(debt_path):
            for l in open(debt_path, encoding="utf-8"):
                l = l.strip()
                if l:
                    try:
                        hist.append(json.loads(l))
                    except Exception:
                        pass
        if not any(h.get("date") == today for h in hist):
            hist.append({"date": today, "debt": debt})
            with open(debt_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"date": today, "debt": debt}, ensure_ascii=False) + "\n")
        old = hist[0]["debt"] if hist else debt
        drop_pct = round(100.0 * (old - debt) / old, 1) if old else 0.0
    except Exception:
        debt, drop_pct = None, None

    rows = []
    stops = []
    for ln in lines:
        lid = ln.get("id")
        m = per.get(lid)
        if not m:
            continue
        closed = m["done"] + m["failed"] - m["blocked"]
        pass_rate = round(100.0 * m["first_pass"] / closed, 1) if closed > 0 else None
        rows.append({
            "line": lid, "name": ln.get("name"), "priority": ln.get("priority"),
            "status": ln.get("status"),
            "cards": m["cards"], "done": m["done"], "failed": m["failed"],
            "first_pass_rate_pct": pass_rate,
            "rework": m["rework"],
            "output_age_h": age_by_line.get(lid),
            "cost_cny": round(m["seconds"] / 3600.0 * rate, 2),
            "reuse_pct": None,   # 资产库建成后回填；无数据不编
        })
        # 自动停线：7 天零产出 且 有在册卡；或 一次过闸率 <50% 且 返工 >=3
        # 冷却不是死刑（2026-11-03）：停线会同时停掉出卡供给（line_plan 认 PAUSED），
        # 指标因此冻结、永远不可能恢复。改成 24h 冷却，到期自动回 ACTIVE 并注明。
        age = age_by_line.get(lid)
        stale = (age is not None and age > 24 * 7 and m["cards"] > 0)
        poor = (pass_rate is not None and pass_rate < 50 and m["rework"] >= 3
                and m["blocked"] < m["failed"])
        if ln.get("status") == "ACTIVE" and (stale or poor):
            stops.append({"line": lid, "why": "7天零产出" if stale else "过闸率<50%且返工>=3",
                          "pass_rate_pct": pass_rate, "rework": m["rework"],
                          "blocked_cards": m["blocked"]})

    # 模型账（CEO 2026-11-02：简单的走本地，省云端 token）：每天看三个数。
    budget = jload(os.path.join(FLEET, "dispatcher", "cloud-budget.json"), {}) or {}
    model_acct = {"cloud_calls": int(budget.get("calls") or 0),
                  "cloud_spent_credits": int(budget.get("spent_credits") or 0),
                  "cloud_cap_credits": int(budget.get("daily_cap_credits") or 0),
                  "local_note": "本地调用见 JUDGMENT-QUEUE 的 model=local:* 与 DIGEST.md"}

    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "rate_cny_per_hour": rate, "lines": rows, "autostop": stops,
           "model": model_acct,
           "debt": debt, "debt_drop_pct": drop_pct,
           "debt_deadline": "30 天内降 30%（每周约 10%）"}
    with open(os.path.join(STATE, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    applied = []
    resumed = []
    if "--no-autostop" not in argv:
        if stops:
            for s in stops:
                for ln in lines:
                    if ln.get("id") != s["line"]:
                        continue
                    # CEO 钦点的线不许被指标闸静默停掉（2026-11-03 实测：asset-lib 因缺输入类
                    # 失败被判过闸率<50%，停线同时停供给，指标冻结后永远回不来）。
                    # 钦点=人已在上层决定要做，机器只能报红，不能替代这个决策。
                    if ln.get("no_autostop") or ln.get("ceo_pinned"):
                        continue
                    ln["status"] = "PAUSED"
                    ln["pause_reason"] = "auto-stop:%s（%s）" % (s["why"], out["ts"][:10])
                    ln["autostop_at"] = out["ts"]
                    ln["resume_hint"] = ("冷却 %dh 后自动回 ACTIVE；期间出卡方停供。"
                                         "CEO 令停/判负的线不在此列（pause_reason 不带 auto-stop）"
                                             % AUTOSTOP_COOLDOWN_H)
                    applied.append(s["line"])
        # 冷却到期自动回线：停线同时停掉供给，指标冻结，没有这一条就永远回不来。
        for ln in lines:
            ts0 = ln.get("autostop_at")
            if ln.get("status") != "PAUSED" or not str(ln.get("pause_reason") or "").startswith("auto-stop"):
                continue
            if not ts0:
                # 旧版只写了日期没写时间戳：补一个，否则这些线永久冻结（2026-11-03 实测
                # bigstream-mv / asset-lib 都停在这个状态，没有任何恢复路径）。
                m0 = re.search(r"（(\d{4}-\d{2}-\d{2})）", str(ln.get("pause_reason") or ""))
                ts0 = (m0.group(1) + "T00:00:00") if m0 else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                ln["autostop_at"] = ts0
            try:
                dt = datetime.fromisoformat(str(ts0))
            except Exception:
                continue
            if (datetime.now() - dt).total_seconds() >= AUTOSTOP_COOLDOWN_H * 3600:
                ln["status"] = "ACTIVE"
                ln["pause_reason"] = "auto-resume:%s 冷却到期（原：%s）" % (
                    datetime.now().strftime("%Y-%m-%d"), ts0[:10])
                ln.pop("autostop_at", None)
                resumed.append(ln.get("id"))
        if applied or resumed:
            json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out["resumed"] = resumed

    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    print("线 %-20s %-4s %-6s %-6s %-8s %-6s %-8s %s" %
          ("", "优先", "过闸率", "返工", "产出年龄", "成本", "卡/完/败", "状态"))
    for r in rows:
        print("   %-20s %-4s %-6s %-6s %-8s %-6s %-8s %s" % (
            r["line"][:20], r["priority"] or "-",
            ("%.0f%%" % r["first_pass_rate_pct"]) if r["first_pass_rate_pct"] is not None else "-",
            r["rework"],
            ("%.1fh" % r["output_age_h"]) if r["output_age_h"] is not None else "-",
            "¥%.2f" % r["cost_cny"],
            "%d/%d/%d" % (r["cards"], r["done"], r["failed"]),
            r["status"]))
    print("模型账：云端 %d 次 / %d 积分（上限 %d）；周期件禁云，默认本地" % (
        model_acct["cloud_calls"], model_acct["cloud_spent_credits"], model_acct["cloud_cap_credits"]))
    if debt is not None:
        print("结构债 %s 条，累计下降 %s%%（目标：30 天降 30%%）" % (debt, drop_pct))
    if applied:
        print("自动停线：%s（可在注册表改回 ACTIVE 恢复）" % "、".join(applied))
    elif stops:
        print("自动停线候选：%s" % "、".join("%s(%s)" % (s["line"], s["why"]) for s in stops))
    print("-> cph4/fleet/state/metrics.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))