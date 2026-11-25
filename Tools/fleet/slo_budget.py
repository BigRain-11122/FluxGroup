#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slo_budget.py — 从盘上事实算 SLI 与剩余错误预算（模型不参与）。

为什么要它（`cph4/fleet/CAPABILITY-DIMENSIONS-v1.md` 落地计划第 2 项）：
红线写在文档里 = 没人检查；变成指标才会每天算。参数全部取自
`cph4/fleet/SERVICE-LEVEL-v1.json`（services/slo/burn_rate/window_days），
本器不自己发明阈值。

诚实边界（这是本器最重要的设计）：
  · 某个服务找不到数据源 → 输出 **NO-DATA**，绝不填 1.0 冒充健康；
  · 回执里没有 rc 的不计入 execution 分母（不把"没记录"当"失败"或"成功"）；
  · 窗口是滚动天级，不做 5 分钟即时快燃——快燃那档只在有秒级样本时才有意义，
    本器明确标注"窗口级燃烧率"，不假装是 SRE 的即时告警。

用法：
  python3 Tools/fleet/slo_budget.py            # 出表并写 OPS-METRICS.md
  python3 Tools/fleet/slo_budget.py --json
  python3 Tools/fleet/slo_budget.py --self-test
退出码：0 全部可算且未破预算 / 1 有服务破预算 / 2 有服务 NO-DATA / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SPEC = os.path.join(FLEET, "SERVICE-LEVEL-v1.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
GZH_LEDGER = os.path.join(FLEET, "social", "gzh", "LOOP-LEDGER.jsonl")
BOARD = os.path.join(FLEET, "OPS-METRICS.md")


def _j(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:                                   # noqa: BLE001
        return d


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def _within(rec, days, key="ts"):
    """只算窗口内的记录。时间戳解析不了的一律算窗口内（宁严不松）。"""
    t = rec.get(key) or ""
    try:
        return datetime.fromisoformat(str(t)[:19]) >= datetime.now() - timedelta(days=days)
    except ValueError:
        return True


# ---------------- 各服务的 SLI（每个都写明数据源） ----------------

def sli_dispatch(days):
    """派卡成交：**DONE 且交付物可判** / 有 owner 的卡。源=PRODUCTION-QUEUE.jsonl。

    口径纠错（2026-11-25 实测）：第一版只算 state==DONE，偏离了
    SERVICE-LEVEL 的定义（要求"交付物可判"）。而且 83 张 CANCELLED 与
    6 张 FAILED 混在一个分母里，会把"正常取消"算成"没成交"。
    现在报三个数，主判用**最严**的那个（不给取消留后门）：
      strict   = DONE且可判 / 全部有 owner 的卡
      excl_cancel = DONE且可判 / (有 owner 且非 CANCELLED)
    """
    rows = [r for r in _rows(QUEUE) if r.get("owner") and _within(r, days)]
    if not rows:
        return None, None, "队列里窗口内没有带 owner 的卡", "PRODUCTION-QUEUE.jsonl", {}
    def is_done(r):
        return str(r.get("state")).upper() == "DONE"

    def judgeable(r):
        return bool(r.get("deliverable") or r.get("accept"))

    good = [r for r in rows if is_done(r) and judgeable(r)]
    cancelled = [r for r in rows if str(r.get("state")).upper() == "CANCELLED"]
    non_cancel = len(rows) - len(cancelled)
    strict = len(good) / len(rows)
    excl = (len(good) / non_cancel) if non_cancel else None
    extra = {"good": len(good), "owned": len(rows), "cancelled": len(cancelled),
             "sli_excl_cancel": round(excl, 4) if excl is not None else None}
    why = ("strict %d/%d；剔取消后 %d/%d=%s"
           % (len(good), len(rows), len(good), non_cancel,
              round(excl, 3) if excl is not None else "-"))
    return strict, len(rows), why, "PRODUCTION-QUEUE.jsonl", extra


def sli_execution(days):
    """执行成功：有 rc 的回执里 rc 在 ok_rc / =0 的比例。源=queue-receipts/*.json。"""
    if not os.path.isdir(RECEIPTS):
        return None, None, "没有 queue-receipts 目录", "queue-receipts/", {}
    ok = n = 0
    for fn in os.listdir(RECEIPTS):
        if not fn.endswith(".json"):
            continue
        d = _j(os.path.join(RECEIPTS, fn), {}) or {}
        if "rc" not in d or not _within(d, days):
            continue                     # 没有 rc 的不进分母：不把"没记录"当结论
        n += 1
        ok_rc = d.get("ok_rc")
        if (isinstance(ok_rc, list) and d["rc"] in ok_rc) or (ok_rc is None and d["rc"] == 0):
            ok += 1
    if n == 0:
        return None, None, "窗口内没有带 rc 的回执", "queue-receipts/", {}
    return ok / n, n, "%d/%d rc 合格" % (ok, n), "queue-receipts/", {}


def sli_pulse(days):
    """脉轮次健康：没有 CRASHED 的轮次占比。源=gzh LOOP-LEDGER。
    口径声明：DEFER/BLOCKED-SUPPLY 是**决策**不是故障，计入健康；只有 CRASHED 记不健康。"""
    rows = [r for r in _rows(GZH_LEDGER) if _within(r, days)]
    if not rows:
        return None, None, "窗口内没有轮次记录", "gzh/LOOP-LEDGER.jsonl", {}
    bad = [r for r in rows if str(r.get("status")).upper() == "CRASHED"]
    return (len(rows) - len(bad)) / len(rows), len(rows), \
        "%d 轮，%d 崩溃" % (len(rows), len(bad)), "gzh/LOOP-LEDGER.jsonl", {}


def sli_sync(days):
    """同步成功：需要"每轮 git 拉/推"的台账。当前**没有轮次台账**，故 NO-DATA。

    现有 `state/state-sync.json` 只存"最后一次成功时间 + 失败清单"，算不出占比，
    所以不拿它硬凑 SLI（差一点点就成假绿）。把它当上下文报出来，让人一眼看到新鲜度。
    """
    ctx = _j(os.path.join(FLEET, "state", "state-sync.json"), {}) or {}
    ok_ts = ctx.get("ok_ts")
    age_h = None
    if isinstance(ok_ts, (int, float)) and ok_ts > 0:
        age_h = round((datetime.now().timestamp() - ok_ts) / 3600.0, 1)
    tail = ("；上下文：上次同步成功 %s 小时前，失败记录 %d 条"
            % (age_h, len(ctx.get("fails") or []))) if age_h is not None else ""
    for cand in ("SYNC-LEDGER.jsonl", "state/sync-ledger.jsonl"):
        p = os.path.join(FLEET, cand)
        if os.path.exists(p):
            rows = [r for r in _rows(p) if _within(r, days)]
            if not rows:
                return None, None, "台账在但窗口内无记录" + tail, cand, {}
            ok = sum(1 for r in rows if r.get("ok"))
            return ok / len(rows), len(rows), "%d/%d 成功%s" % (ok, len(rows), tail), cand, {}
    # 为什么不能"顺手修好"（2026-11-25 查实）：
    #   1) 同步守护 com.fluxgroup.statesync 自 2026-11-11 按 CEO 令暂停，
    #      plist 在 ~/Library/LaunchAgents/disabled/20261111-pause/；
    #   2) 它会 git push origin main，而当前仓里有指向 ~/BigLoom 的**绝对路径软链**，
    #      一推出去，任何拉取的机器都会看到断链。
    # 所以这条保持 NO-DATA，并写明恢复的两个前置条件，而不是填个好看的数字。
    return (None, None,
            "同步守护自 2026-11-11 按 CEO 令暂停（plist 在 disabled/20261111-pause/），"
            "且恢复前必须先解决 BigLoom 绝对路径软链——否则一 push 就把异机弄断。"
            "只有最后成功时间，算不出轮次占比" + tail,
            "state/state-sync.json", {"paused_by": "CEO-20261111",
                                     "blocker": "bigloom-absolute-symlink"})


def sli_demand(days):
    """需求机检通过：**OK / (OK + GAP)**，人判项（UNVERIFIED）不计入。
    源=`state/demand-audit.json`（demand_audit.py 产出）。超窗视为过期 → NO-DATA。"""
    p = os.path.join(FLEET, "state", "demand-audit.json")
    d = _j(p, {}) or {}
    if not d.get("counts"):
        return None, None, "没有需求审计结果", "state/demand-audit.json", {}
    ts = str(d.get("ts") or "")
    try:
        age_d = (datetime.now() - datetime.fromisoformat(ts[:19])).days
    except ValueError:
        age_d = None
    if age_d is not None and age_d > days:
        return (None, None, "需求审计结果已 %d 天未刷新（窗口 %d 天）" % (age_d, days),
                "state/demand-audit.json", {"stale_days": age_d})
    c = d["counts"]
    ok = int(c.get("OK") or 0)
    gap = int(c.get("GAP") or 0)
    unv = int(c.get("UNVERIFIED") or 0)
    if ok + gap == 0:
        return None, None, "OK+GAP 为 0，无法计算", "state/demand-audit.json", {}
    extra = {"ok": ok, "gap": gap, "unverified": unv, "age_days": age_d}
    why = "OK %d / (OK %d + GAP %d)=%.3f；人判 %d 项不计" % (ok, ok, gap, ok / (ok + gap), unv)
    return ok / (ok + gap), ok + gap, why, "state/demand-audit.json", extra


SLI_FN = {"dispatch": sli_dispatch, "execution": sli_execution,
          "pulse": sli_pulse, "sync": sli_sync, "demand": sli_demand}


def compute(spec=None, days=None):
    spec = spec or _j(SPEC, {}) or {}
    days = days or spec.get("window_days") or 7
    br = spec.get("burn_rate") or {}
    out = []
    for s in spec.get("services") or []:
        sid = s.get("id")
        fn = SLI_FN.get(sid)
        if not fn:
            out.append({"id": sid, "name": s.get("name"), "slo": s.get("slo"),
                        "sli": None, "n": None, "state": "NO-DATA",
                        "why": "本器还没接这个服务的数据源", "source": "-"})
            continue
        sli, n, why, source, extra = fn(days)
        if sli is None:
            out.append({"id": sid, "name": s.get("name"), "slo": s.get("slo"),
                        "sli": None, "n": n, "state": "NO-DATA",
                        "why": why, "source": source})
            continue
        slo = float(s.get("slo") or 0)
        budget = max(1e-9, 1 - slo)
        burn = (1 - sli) / budget
        state = "OK" if sli >= slo else ("WARN" if burn < (br.get("slow") or {}).get("multiple", 6)
                                         else "BREACH")
        out.append({"id": sid, "name": s.get("name"), "slo": slo, "sli": round(sli, 4),
                    "n": n, "state": state, "why": why, "source": source,
                    "extra": extra,
                    "budget_left": round(max(0.0, sli - slo) / budget, 3),
                    "burn_multiple": round(burn, 2)})
    return {"ts": datetime.now().isoformat(timespec="seconds"), "window_days": days,
            "services": out}


def render(r):
    L = ["# 运营指标（OPS-METRICS）", "",
         "> 由 `Tools/fleet/slo_budget.py` 生成，参数取 `SERVICE-LEVEL-v1.json`。",
         "> SLI 一律由盘上事实算；算不出来的写 **NO-DATA**，不填好看的数字。", "",
         "- 时间：%s｜窗口：%d 天" % (r["ts"], r["window_days"]), "",
         "| 服务 | SLO | SLI | 样本 | 状态 | 数据源 | 说明 |",
         "|---|---|---|---|---|---|---|"]
    for s in r["services"]:
        L.append("| %s | %s | %s | %s | **%s** | `%s` | %s |" % (
            s.get("name") or s["id"],
            s.get("slo") if s.get("slo") is not None else "-",
            s["sli"] if s["sli"] is not None else "-",
            s["n"] if s["n"] is not None else "-",
            s["state"], s["source"], s.get("why") or ""))
    nd = [s for s in r["services"] if s["state"] == "NO-DATA"]
    br = [s for s in r["services"] if s["state"] == "BREACH"]
    L += ["", "结论：%d 项可算，%d 项 NO-DATA，%d 项破预算。"
          % (len(r["services"]) - len(nd), len(nd), len(br))]
    if nd:
        L.append("")
        L.append("NO-DATA 不是健康——它只是「我们还没测」。要补的是台账，不是阈值。")
    return "\n".join(L)


# ---------------- 自检 ----------------

def self_test():
    import shutil
    import tempfile
    cases = []
    d = tempfile.mkdtemp(prefix="slo-")
    saved = (globals()["QUEUE"], globals()["RECEIPTS"], globals()["GZH_LEDGER"], globals()["BOARD"])
    try:
        globals()["QUEUE"] = os.path.join(d, "q.jsonl")
        globals()["RECEIPTS"] = os.path.join(d, "rc")
        globals()["GZH_LEDGER"] = os.path.join(d, "loop.jsonl")
        os.makedirs(globals()["RECEIPTS"], exist_ok=True)

        now = datetime.now().isoformat(timespec="seconds")
        # 10 张有 owner 的卡：8 张 DONE 且带交付物、1 张 DONE 但无交付物（负控）、
        # 1 张开着；另加 2 张 CANCELLED 用来验"剔取消后"的第二个数
        with open(globals()["QUEUE"], "w") as f:
            for i in range(8):
                f.write(json.dumps({"owner": "m", "state": "DONE",
                                    "deliverable": "d%d.md" % i, "ts": now}) + "\n")
            f.write(json.dumps({"owner": "m", "state": "DONE", "ts": now}) + "\n")   # 无交付物
            f.write(json.dumps({"owner": "m", "state": "OPEN", "ts": now}) + "\n")
            f.write(json.dumps({"owner": "m", "state": "CANCELLED", "ts": now}) + "\n")
            f.write(json.dumps({"owner": "m", "state": "CANCELLED", "ts": now}) + "\n")
        for i in range(4):
            json.dump({"rc": 0 if i < 3 else 1, "ts": now},
                      open(os.path.join(globals()["RECEIPTS"], "r%d.json" % i), "w"))
        # 无 rc 的回执：用来验"没记录不进分母"。夹具本身必须真的没有 rc
        json.dump({"ts": now, "outcome": "unknown"},
                  open(os.path.join(globals()["RECEIPTS"], "no_rc.json"), "w"))
        with open(globals()["GZH_LEDGER"], "w") as f:
            for st in ["OK", "DEFER", "BLOCKED-SUPPLY", "CRASHED"]:
                f.write(json.dumps({"status": st, "ts": now}) + "\n")

        spec = {"window_days": 7, "burn_rate": {"slow": {"multiple": 6}},
                "services": [{"id": "dispatch", "name": "派卡成交", "slo": 0.9},
                             {"id": "execution", "name": "执行成功", "slo": 0.88},
                             {"id": "pulse", "name": "脉轮次健康", "slo": 0.95},
                             {"id": "sync", "name": "同步成功", "slo": 0.85},
                             {"id": "unknown", "name": "没接的", "slo": 0.9}]}
        r = compute(spec)
        by = {s["id"]: s for s in r["services"]}

        # compute() 里 sli 已四舍五入到 4 位，容差不能取 1e-9
        cases.append(("dispatch = 8/12（DONE 且带交付物 / 有 owner）",
                      abs(by["dispatch"]["sli"] - 8 / 12) < 1e-3))
        cases.append(("负控[DONE 但无交付物] 不计入分子",
                      by["dispatch"]["extra"]["good"] == 8))
        cases.append(("剔取消后 = 8/10", abs(by["dispatch"]["extra"]["sli_excl_cancel"] - 0.8) < 1e-3))
        cases.append(("dispatch 未达 SLO 判非 OK", by["dispatch"]["state"] != "OK"))
        cases.append(("execution 只算有 rc 的 4 条", by["execution"]["n"] == 4))
        cases.append(("execution SLI=0.75", abs(by["execution"]["sli"] - 0.75) < 1e-3))
        cases.append(("execution 破预算", by["execution"]["state"] in ("WARN", "BREACH")))
        cases.append(("pulse 把 DEFER/BLOCKED 算健康", by["pulse"]["sli"] == 0.75))
        cases.append(("负控[无数据源] 必须 NO-DATA", by["sync"]["state"] == "NO-DATA"))
        cases.append(("负控[未接服务] 必须 NO-DATA", by["unknown"]["state"] == "NO-DATA"))
        cases.append(("负控[NO-DATA 不许填 sli=1]", by["sync"]["sli"] is None))

        # 负控：把队列清空 → dispatch 必须 NO-DATA（不是 0，也不是 1）
        open(globals()["QUEUE"], "w").close()
        r2 = compute(spec)
        by2 = {s["id"]: s for s in r2["services"]}
        cases.append(("负控[队列空] 必须 NO-DATA", by2["dispatch"]["state"] == "NO-DATA"))
    finally:
        (globals()["QUEUE"], globals()["RECEIPTS"], globals()["GZH_LEDGER"],
         globals()["BOARD"]) = saved
        shutil.rmtree(d, ignore_errors=True)

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    r = compute()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        os.makedirs(os.path.dirname(BOARD), exist_ok=True)
        open(BOARD, "w", encoding="utf-8").write(render(r))
        print(render(r))
        print("\n→ %s" % os.path.relpath(BOARD, ROOT))
    nd = [s for s in r["services"] if s["state"] == "NO-DATA"]
    br = [s for s in r["services"] if s["state"] == "BREACH"]
    if br:
        return 1
    return 2 if nd else 0


if __name__ == "__main__":
    sys.exit(main())
