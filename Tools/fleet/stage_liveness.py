#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stage_liveness.py - 证明「每个登记的阶段真的在跑」，而不是只写在节奏表里。

CEO 2026-11-07：「你好好帮我再弄一下，我感觉还是不放心」。

不放心有具体来源：PULSE.json 每轮整份覆盖，慢批阶段又每 300 秒才跑一部分，
所以看一屏永远只能看到「这一轮跑了什么」，看不出「某个阶段是不是已经三小时没跑了」。
历史上的两个真事故正长在这个盲区里：
  · ops_metrics 与 metrics 是同一个工具登记两次，两处契约相反 → 永久红；
  · verify_done 登记在节奏表、脉里从未接线 → 91 张 DONE 无人过问。

本席只做一件事：拿 stage-last.json（脉每轮写的"最后一次真跑"）对节奏表的周期，
逐个阶段判 STALE。判据是**周期×2 或 600 秒取大**——慢批的 300 秒节流不算异常。

用法：
  python3 Tools/fleet/stage_liveness.py           # 一屏 + rc
  python3 Tools/fleet/stage_liveness.py --json    # 机读
退出码：0 全部新鲜 / 1 有阶段超期未跑 / 2 没有取到记录（无法判定）
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
LAST = os.path.join(STATE, "stage-last.json")
BOARD = os.path.join(F, "STAGE-LIVENESS.md")
GRACE_S = 600

# 已知会因为外因而长期不跑的阶段（写在这里而不是调阈值，避免"调到看不见"）
DORMANT_OK = {
    "eventlog": "NATS 总线不可达时按熔断跳过（可达即跑）",
    "executor_guard": "远端探针，机器不在线时如实记 unreachable",
}


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def periods():
    """从节奏表（COMMAND-CADENCE-v3.json，由 cadence_build 从 STAGES 生成）取周期。
    取不到就按慢批 300 秒算——宁可宽一点，也不要制造假红。"""
    tab = jload(os.path.join(F, "COMMAND-CADENCE-v3.json"), {}) or {}
    out = {}
    for t in (tab.get("tasks") or []):
        st = str(t.get("stage") or "")
        if st:
            out[st] = float(t.get("period_s") or 0)
    return out


def disabled():
    """脉按瘦身策略主动跳过的阶段（AUTONOMY-CONFIG.pulse.disabled_stages + canary 降频）。
    它们不跑是设计态，报成"从未跑"就是假红——这正是资产面最伤信任的那种红。"""
    cfg = jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}
    pol = cfg.get("pulse") or {}
    off = set(pol.get("disabled_stages") or [])
    if int(pol.get("canary_every_cycles") or 1) > 1:
        off.add("canary")      # 降频跑的，周期不由节奏表反映
    return off


def _age_s(ts):
    """ts 形如 2026-11-07T22:45:05+08:00。带时区偏移，不能直接 strptime %H:%M:%S——
    首版就是这么写的，结果 89 条记录全判超期（自己造了一次假红）。"""
    s = str(ts or "")
    try:
        return datetime.now().timestamp() - datetime.fromisoformat(s).timestamp()
    except Exception:
        pass
    try:
        return datetime.now().timestamp() - datetime.strptime(
            s.split("+")[0].split("Z")[0][:19], "%Y-%m-%dT%H:%M:%S").timestamp()
    except Exception:
        return None


def audit():
    sys.path.insert(0, HERE)
    import master_pulse as mp
    last = jload(LAST, None)
    if not last:
        return {"verdict": "UNKNOWN", "rows": [],
                "why": "没有 stage-last.json（脉还没写过）", "rc": 2}
    per = periods()
    off = disabled()
    rows = []
    for name, _argv, _to, ok_rc, _slow in mp.STAGES:
        if name in off:
            rows.append({"stage": name, "state": "SKIPPED", "age_s": None,
                         "period_s": per.get(name), "rc": None})
            continue
        rec = last.get(name)
        if not rec:
            rows.append({"stage": name, "state": "NEVER", "age_s": None,
                         "period_s": per.get(name), "rc": None})
            continue
        age = _age_s(rec.get("ts"))
        p = per.get(name) or 0
        limit = max(p * 2, GRACE_S) if p else GRACE_S
        st = "OK" if (age is not None and age <= limit) else "STALE"
        rows.append({"stage": name, "state": st,
                     "age_s": round(age, 1) if age is not None else None,
                     "period_s": p or None, "rc": rec.get("rc"),
                     "ok_rc": sorted(ok_rc), "limit_s": limit})
    stale = [r for r in rows if r["state"] == "STALE"]
    never = [r for r in rows if r["state"] == "NEVER"]
    return {"verdict": "FAIL" if (stale or never) else "PASS", "rows": rows,
            "stale": [r["stage"] for r in stale], "never": [r["stage"] for r in never],
            "rc": 1 if (stale or never) else 0}


def board(res):
    rows = res.get("rows") or []
    stale = res.get("stale") or []
    never = res.get("never") or []
    skipped = sorted(r["stage"] for r in rows if r["state"] == "SKIPPED")
    L = ["# 阶段自证（每个登记阶段是否真的在跑）%s" % now(), "",
         "判据：最后一次**真跑**（rc 非空）距今 ≤ 周期×2 与 600 秒的较大者。"
         "「PULSE 里没显示」不等于没跑——慢批 300 秒节流是设计态。", "",
         "共 %d 个阶段：新鲜 %d · 超期 %d · 从未跑 %d · 瘦身跳过 %d" % (
             len(rows), len(rows) - len(stale) - len(never) - len(skipped),
             len(stale), len(never), len(skipped)), ""]
    if res["verdict"] == "UNKNOWN":
        L += ["**无法判定**：%s" % res.get("why")]
    elif not stale and not never:
        L += ["**全部 %d 个阶段新鲜。**" % len(rows)]
    else:
        L += ["**%d 个超期未跑 / %d 个从未跑过。**" % (len(stale), len(never)), ""]
        L += ["| 阶段 | 状态 | 距今 | 周期 | 返回码 |", "|---|---|---|---|---|"]
        for r in rows:
            if r["state"] == "NEVER":
                L.append("| %s | 从未跑过 | - | %s | - |" % (r["stage"], r.get("period_s")))
        for r in rows:
            if r["state"] == "STALE":
                L.append("| %s | 超期 | %.0fs | %ss | %s |" % (
                    r["stage"], r["age_s"] or -1, r.get("period_s"), r.get("rc")))
    dormant = [r for r in rows if r["stage"] in DORMANT_OK]
    if skipped:
        L += ["", "## 瘦身跳过（设计态，不是缺陷）", "",
              "- " + "、".join(skipped)]
    if dormant:
        L += ["", "## 已知长期不跑（外因，不是缺陷）", ""]
        for r in dormant:
            L.append("- %s：%s" % (r["stage"], DORMANT_OK[r["stage"]]))
    L += ["", "---", "_这份屏只回答问题「它到底跑没跑过」；跑得对不对由各席自己的判据管_"]
    return "\n".join(L) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    res = audit()
    txt = board(res)
    os.makedirs(STATE, exist_ok=True)
    try:
        open(BOARD, "w", encoding="utf-8").write(txt)
        with open(os.path.join(STATE, "stage-liveness.json"), "w", encoding="utf-8") as f:
            json.dump({"ts": now(), **res}, f, ensure_ascii=False, indent=1)
    except Exception as e:
        print("W-LIVENESS-WRITE %s" % str(e)[:80])

    if a.json:
        print(json.dumps({"ts": now(), "verdict": res["verdict"],
                          "stale": res.get("stale"), "never": res.get("never")},
                         ensure_ascii=False))
    else:
        print(txt)
    print("[liveness] %s · 超期 %d · 从未跑 %d -> rc=%d" % (
        res["verdict"], len(res.get("stale") or []), len(res.get("never") or []), res["rc"]))
    return res["rc"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))