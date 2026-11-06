# -*- coding: utf-8 -*-
"""model_plan.py - 模型侧排班体检：现在驻留多少、超没超预算、矩阵与策略是否一致。

Why: 2026-11-07 实测三模型同时驻留 10.4GB（其中 3.7GB 是不该常驻的备用档），根因是
两份策略文件各写一个"现役模型"，且驻留判据用同族前缀。这台机器每天核对三件事，
让"合理安排"不靠人记：
  1. 驻留是否超预算（常驻 8GB / 峰值 10GB）；
  2. 矩阵里出现的模型名是否都在 LOCAL-MODEL-POLICY（单一源）；
  3. 每个 P0 任务是否有降级路径（模型挂了不能停线）。

Usage: model_plan.py [--json]
Exit: 0 合规；1 有告警；2 配置缺失
"""
import argparse
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
MATRIX = os.path.join(FLEET, "MODEL-MONITOR-MATRIX-v1.json")
LOCAL = os.path.join(FLEET, "LOCAL-MODEL-POLICY.json")
out_board = os.path.join(FLEET, "MODEL-PLAN.md")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def resident():
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            ms = json.load(r).get("models", [])
        return [{ "name": m.get("name"), "gb": round((m.get("size") or 0) / 1024 ** 3, 1),
                  "expires": str(m.get("expires_at") or "")[:19]} for m in ms]
    except Exception as e:
        return {"_error": str(e)[:80]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    mx = jload(MATRIX)
    lp = jload(LOCAL)
    if not mx or not lp:
        print(json.dumps({"verdict": "E-CONFIG", "detail": "矩阵或策略缺失"}, ensure_ascii=False))
        return 2

    duties = lp.get("duties") or {}
    known = {((duties.get(k) or {}).get("model") or "").strip()
             for k in ("resident", "embedding", "longform", "sealed", "alternative")}
    known.discard("")
    seats = mx.get("seats") or {}
    budget = mx.get("budget") or {}
    warns, errs = [], []

    # 1) 矩阵不得另立模型名
    for sid, s in seats.items():
        m = str((s or {}).get("model") or "").strip()
        if m and m not in known:
            errs.append("E-NAME: 座位 %s 的模型 %s 不在 LOCAL-MODEL-POLICY（单一源）" % (sid, m))

    # 2) P0 必须有降级
    for t in mx.get("tasks") or []:
        if str(t.get("tier")) == "P0" and not str(t.get("degrade") or "").strip() \
                and t.get("seat") != "rule":
            errs.append("E-DEGRADE: P0 任务 %s 无降级路径（模型挂了会停线）" % t.get("id"))

    # 3) 驻留与预算
    live = resident()
    if isinstance(live, dict):
        peak = None
        warns.append("W-OLLAMA: 读不到驻留（%s），本项跳过" % live.get("_error"))
    else:
        peak = round(sum(x["gb"] for x in live), 1)
        cap = float(budget.get("resident_cap_gb") or 8.0)
        hard = float(budget.get("peak_cap_gb") or 10.0)
        if peak > hard:
            errs.append("E-MEM: 驻留 %.1fGB 超峰值上限 %.1fGB" % (peak, hard))
        elif peak > cap:
            warns.append("W-MEM: 驻留 %.1fGB 超常驻上限 %.1fGB" % (peak, cap))
        for x in live:
            if x["name"] not in known:
                warns.append("W-STRAY: %s 不在白名单，应让位" % x["name"])

    verdict = "FAIL" if errs else ("WARN" if warns else "PASS")
    L = ["# 模型排班 %s" % __import__("time").strftime("%Y-%m-%dT%H:%M:%S"), ""]
    L.append("判据：**%s**｜常驻上限 %sGB / 峰值 %sGB / 办公预留 %sGB"
             % (verdict, budget.get("resident_cap_gb"), budget.get("peak_cap_gb"),
                budget.get("office_reserve_gb")))
    L.append("")
    L.append("## 现在驻留")
    L.append("")
    if isinstance(live, dict):
        L.append("- 读不到 ollama（%s）" % live.get("_error"))
    else:
        for x in live:
            L.append("- %s **%.1fGB**｜到期 %s" % (x["name"], x["gb"], x["expires"]))
        L.append("- 合计 **%.1fGB**，留给办公与车道 %.1fGB"
                 % (peak, 32.0 - (peak or 0)))
    L.append("")
    L.append("## 任务怎么排（谁用模型、谁不许用）")
    L.append("")
    for t in sorted(mx.get("tasks") or [], key=lambda x: str(x.get("tier"))):
        L.append("- %s [%s] %s → **%s**｜%s%s"
                 % (t.get("id"), t.get("tier"), t.get("name"), t.get("seat"),
                    t.get("cad"), ("｜降级：" + str(t.get("degrade"))) if t.get("degrade") else ""))
    L.append("")
    L.append("## 并发与轮转")
    L.append("")
    rot = mx.get("rotation") or {}
    for k in ("order", "rule", "preempt", "dedupe"):
        v = rot.get(k)
        if isinstance(v, list):
            v = " > ".join(v)
        if v:
            L.append("- %s：%s" % (k, v))
    L.append("")
    if errs or warns:
        L.append("## 需要处理")
        L.append("")
        for e in errs:
            L.append("- ❌ %s" % e)
        for w in warns:
            L.append("- ⚠ %s" % w)
        L.append("")
    with open(out_board, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(json.dumps({"verdict": verdict, "resident_gb": peak, "errors": len(errs),
                      "warnings": len(warns), "board": os.path.relpath(out_board, ROOT)},
                     ensure_ascii=False))
    for x in errs[:6]:
        print("  ERROR", x)
    for x in warns[:6]:
        print("  WARN ", x)
    return 2 if errs else (1 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())