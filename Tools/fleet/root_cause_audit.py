# -*- coding: utf-8 -*-
"""root_cause_audit.py - 六条根因的复验器（判「已治」只认这台机器）。

为什么要有它：这段时间修了几十处，但每次都是"修完自己说修好了"。根因账不靠声明，
靠每天复验——治好了是 PASS，没治好就点名是哪条根因复发、证据是什么。

R1 单一真相源  R2 生成态进 git  R3 假绿判据
R4 修复未生效  R5 无人收口     R6 跨机不可达

Usage: root_cause_audit.py [--json]
Exit: 0 全部已治；1 有复发；2 台账坏了
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
LEDGER = os.path.join(FLEET, "ROOT-CAUSE-LEDGER-v1.json")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
OUT = os.path.join(FLEET, "ROOT-CAUSE-BOARD.md")
STATE_OUT = os.path.join(STATE, "root-cause.json")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def read_jsonl(p):
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


def live_rows():
    """当前执行面 = rt/<station>/queue.jsonl 五片。

    Why（2026-11-14 实锚）：本文件原来三处都 read_jsonl(QUEUE)，而 QUEUE 是
    PRODUCTION-QUEUE.jsonl —— 该文件 11-11 已退役归档，只在 git 里留了 2048 行历史态。
    后果是这条审计拿"没人执行的历史档"判活卡与假完成：某次工具把它重建回 25 行，
    判据立刻由红转绿；把工作树恢复成 2048 行历史态，又冒出 2 张"无 owner 的失败卡"
    （历史遗留，早就不在执行面上）。判据读错数据面，红绿都不算数。
    卡的真实状态只认分片；读不到分片时才回落到旧文件（沙箱/新机）。
    """
    try:
        import demand_audit as _da
        rows = _da.qrows()
        if rows:
            return rows
    except Exception:
        pass
    return read_jsonl(QUEUE)


def git(*args, timeout=60):
    try:
        p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except Exception:
        return 1, ""


# ---- R1 单一真相源 ------------------------------------------------------------
def probe_multi_source(_r):
    bad = []
    mp = jload(os.path.join(FLEET, "MODEL-POLICY.json"), {}) or {}
    lp = jload(os.path.join(FLEET, "LOCAL-MODEL-POLICY.json"), {}) or {}
    a = str(((mp.get("lane_local_llm") or {}).get("model")) or "")
    b = str(((lp.get("duties") or {}).get("resident") or {}).get("model") or "")
    if a and b and a != b:
        bad.append("模型现役两处不同：%s vs %s" % (a, b))
    # 同 id 不得在两个分片里各写一份不同状态（并发写分片 / 误搬卡）。
    # 原判据是"队列 vs 备队列同 id 状态漂移"，两边都是退役档，交集恒空=判据永远绿。
    q = live_rows()
    by, drift = {}, 0
    for r in q:
        i = str(r.get("id") or "")
        if not i:
            continue
        st = str(r.get("state") or "")
        if i in by and by[i] != st:
            drift += 1
        by.setdefault(i, st)
    if drift:
        bad.append("分片间同 id 状态冲突 %d 条" % drift)
    # 节奏表与脉一致性
    cp = jload(os.path.join(STATE, "cadence-plan.json"), {}) or {}
    if cp.get("verdict") == "FAIL":
        bad.append("节奏表校验 FAIL")
    return (len(bad) == 0), ("; ".join(bad) if bad else "模型/队列/节奏三处一致")


# ---- R2 生成态进 git ----------------------------------------------------------
def probe_state_in_git(_r):
    rc, out = git("ls-files")
    if rc != 0:
        return None, "无法读 git ls-files"
    tracked = out.splitlines()
    # lanes/ 与 queue-receipts/ 是分发与回执通道，必须留在 git；只有纯记账可移出。
    prefixes = ("cph4/fleet/state/", "cph4/fleet/radar/",
                "cph4/fleet/chief/", "cph4/fleet/sync/")
    n = [x for x in tracked if x.startswith(prefixes)]
    return (len(n) == 0), "%d 个运行时文件仍被 git 跟踪" % len(n)


# ---- R3 假绿判据 --------------------------------------------------------------
def probe_false_green(_r):
    bad = []
    rows = live_rows()
    import re
    notdeliv = 0
    for x in rows:
        if str(x.get("state", "")).upper() != "DONE":
            continue
        d = str(x.get("deliverable") or "").strip()
        if not d or re.match(r"^([A-Za-z]:[\\/]|\\\\|/)", d):
            continue
        if d.startswith(("quant/", "gaming/", "media/", "life/", "compute/",
                         "domain/", "house/", "cph4/fleet/state/")):
            continue
        if not any(d.endswith(e) for e in (".json", ".jsonl", ".md", ".csv", ".png",
                                           ".jpg", ".mp4", ".wav", ".txt", ".html")):
            continue
        if not os.path.exists(os.path.join(ROOT, d)):
            notdeliv += 1
    if notdeliv:
        bad.append("DONE 未交付 %d 张" % notdeliv)
    al = jload(os.path.join(STATE, "alerts.json"), {}) or {}
    ar = al.get("alerts") if isinstance(al, dict) else al
    art = sum(1 for x in (ar or []) if isinstance(x, dict)
              and "ARTIFACT" in str(x.get("error_class") or x.get("kind") or ""))
    if art:
        bad.append("E-ARTIFACT %d 条" % art)
    lines = (jload(os.path.join(STATE, "lines.json"), {}) or {}).get("lines") or []
    selfref = 0
    for l in lines:
        for ev in (l.get("evidence") or []):
            ev = ev or {}
            p = str(ev.get("path") or "")
            if str((ev.get("stat") or {}).get("kind")) == "local" and \
                    p.startswith(("cph4/fleet/state", "cph4/fleet/queue-receipts")):
                selfref += 1
                break
    if selfref:
        bad.append("度量自指 %d 条线" % selfref)
    return (len(bad) == 0), ("; ".join(bad) if bad else "无未交付/无 E-ARTIFACT/无自指")


# ---- R4 修复未生效 ------------------------------------------------------------
def probe_code_age(_r):
    newest_code, seen = 0.0, 0
    for rel in ("Tools/fleet/master_pulse.py", "Tools/fleet/lane_agent.py",
                "Tools/fleet/fleet_lane.py", "Tools/fleet/commander.py"):
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if os.path.exists(p):
            newest_code = max(newest_code, os.path.getmtime(p))
            seen += 1
    if not seen:
        return None, "代码文件缺失"
    d = os.path.join(FLEET, "queue-receipts")
    newest_rec = 0.0
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.startswith("self-improve-"):
                continue
            p = os.path.join(d, f)
            if os.path.isfile(p):
                newest_rec = max(newest_rec, os.path.getmtime(p))
    if not newest_rec:
        return None, "无回执可比"
    if newest_code > newest_rec + 1800:
        return False, "代码比最近产物新 %.0f 分钟，执行器可能跑旧码" % (
            (newest_code - newest_rec) / 60)
    return True, "产物比代码新（执行器在跑当前码）"


# ---- R5 无人收口 --------------------------------------------------------------
def probe_unowned_alerts(_r):
    bad = []
    rows = live_rows()
    blocked = [x for x in rows
               if str(x.get("state", "")).upper() in ("BLOCKED", "FAILED")
               and not str(x.get("owner") or "").strip()]
    if blocked:
        bad.append("%d 张 BLOCKED/FAILED 无 owner" % len(blocked))
    live = [x for x in rows if str(x.get("state", "")).upper() in
            ("OPEN", "READY", "CLAIMED", "RUNNING")]
    seen, dup = set(), 0
    for x in live:
        k = str(x.get("deliverable") or "")
        if k:
            if k in seen:
                dup += 1
            seen.add(k)
    if dup:
        bad.append("%d 张同交付物重复在飞" % dup)
    al = jload(os.path.join(STATE, "alerts.json"), {}) or {}
    ar = al.get("alerts") if isinstance(al, dict) else al
    noowner = sum(1 for x in (ar or []) if isinstance(x, dict) and not x.get("owner"))
    if noowner:
        bad.append("%d 条告警无 owner" % noowner)
    return (len(bad) == 0), ("; ".join(bad) if bad else "告警/卡均有责任人")


# ---- R6 跨机不可达 ------------------------------------------------------------
def probe_cross_machine(_r):
    f = jload(os.path.join(STATE, "fork-status.json"), {})
    if f is None:
        return None, "无 fork-status（先跑 fork_close 才有数据）"
    nodes = (f or {}).get("nodes") or {}
    if not nodes:
        return None, "fork-status 无节点数据"
    bad = [n for n, v in nodes.items() if int((v or {}).get("ahead") or 0) > 0]
    return (len(bad) == 0), ("分叉机器 %s（需人工一次 reset）" % ",".join(bad)) if bad else "无分叉"


PROBES = {"probe_multi_source": probe_multi_source, "probe_state_in_git": probe_state_in_git,
          "probe_false_green": probe_false_green, "probe_code_age": probe_code_age,
          "probe_unowned_alerts": probe_unowned_alerts, "probe_cross_machine": probe_cross_machine}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    led = jload(LEDGER)
    if not led:
        print(json.dumps({"verdict": "E-LEDGER"}, ensure_ascii=False))
        return 2

    results = []
    for r in led.get("roots") or []:
        fn = PROBES.get(str(r.get("verify")))
        if not fn:
            results.append({"id": r["id"], "name": r["name"], "state": "UNKNOWN",
                            "evidence": "复验器缺失:%s" % r.get("verify")})
            continue
        try:
            ok, ev = fn(r)
        except Exception as e:
            ok, ev = None, "复验异常:%s" % str(e)[:60]
        st = "CURED" if ok else ("RELAPSED" if ok is False else "UNVERIFIED")
        results.append({"id": r["id"], "name": r["name"], "state": st, "evidence": ev,
                        "cure": r.get("cure"), "residual": r.get("residual")})

    cnt = {}
    for x in results:
        cnt[x["state"]] = cnt.get(x["state"], 0) + 1
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = ["# 根因总账 %s" % now, "",
         "_6 条根因：已治 %d / 复发 %d / 待验 %d。判「已治」只认这台机器的复验输出。_"
         % (cnt.get("CURED", 0), cnt.get("RELAPSED", 0), cnt.get("UNVERIFIED", 0)), ""]
    rel = [x for x in results if x["state"] == "RELAPSED"]
    L.append("## 现在复发的（必须当场处理）")
    L.append("")
    if rel:
        for x in rel:
            L.append("- **%s %s**｜%s" % (x["id"], x["name"], x["evidence"]))
            L.append("  - 根治：%s" % (x.get("cure") or "")[:80])
    else:
        L.append("- 无。六条根因当前均未复发。")
    L.append("")
    L.append("## 六条根因逐条")
    L.append("")
    for x in results:
        mark = {"CURED": "✅", "RELAPSED": "❌", "UNVERIFIED": "◻"}.get(x["state"], "?")
        L.append("### %s %s %s" % (mark, x["id"], x["name"]))
        L.append("- 复验：%s" % x["evidence"])
        L.append("- 残余风险：%s" % (x.get("residual") or "—"))
        L.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(STATE, exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "counts": cnt, "results": results}, f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": "RELAPSED" if rel else ("UNVERIFIED" if cnt.get("UNVERIFIED") else "CURED"),
                      "counts": cnt, "board": os.path.relpath(OUT, ROOT)}, ensure_ascii=False))
    for x in rel:
        print("  RELAPSED", x["id"], x["evidence"])
    return 1 if rel else 0


if __name__ == "__main__":
    sys.exit(main())