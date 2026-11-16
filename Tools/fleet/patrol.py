#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patrol.py - 全年巡查：每天一份覆盖全队的巡查报告，并留历史趋势

为什么要有它（2026-11-16 CEO「拉起机队工作 全年巡查」）：
  主控脉每轮做的是"当下这一轮"，viz_audit 看的是"看板本身"。缺一层
  「跨天看趋势」的东西：今天比昨天多产了几张、阻塞卡是变多还是变少、
  哪台机连续几天不到、模型还跑不跑得动。没有趋势就只能看瞬时绿灯，
  昨天的 20 张和今天的 0 张在页面上长得一模一样。

六个面（每面都要给数字，不给形容词）：
  1. machines   各机 8790 探测 + executor 判定（含龄期，陈旧即标）
  2. queue      各分片 OPEN/RUNNING/BLOCKED/FAILED 计数
  3. output     今日/昨日/7日 交付物卡数（区分交付与流程卡）
  4. blocked    BLOCKED 卡的阻塞原因分类（命令未接/缺产物/机器离线/其他）
  5. model      ollama 版本、模型数、真跑一次 tok/s（失败即标）
  6. silent     静默边界（哨兵 + 自启项数）+ 看板体检结论

产物：
  cph4/fleet/PATROL.md              一屏人读
  cph4/fleet/state/patrol.json      最新一次机读
  cph4/fleet/state/patrol-history.jsonl  每行一天，供趋势

用法：
  python3 Tools/fleet/patrol.py            # 生成（同日重复生成会覆盖当天）
  python3 Tools/fleet/patrol.py --check    # 只打印不落盘
退出码：0 正常 / 2 有关键面不可用（机器/模型）
"""
import argparse
import collections
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT_MD = os.path.join(ROOT, "cph4", "fleet", "PATROL.md")
OUT_JS = os.path.join(STATE, "patrol.json")
HIST = os.path.join(STATE, "patrol-history.jsonl")
NODES = {"bm-a": "100.110.185.62", "bm-b": "100.82.175.0", "bm-c": "100.123.74.104"}
SHARDS = ("control", "delivery", "visual", "audio", "brain")
META = ("TRIAGE", "PLAN", "CHECK", "ENV-PROBE", "CANARY", "PATROL",
        "AUDIT", "PROBE", "SCAN")


def days(n):
    return [time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400 * i))
            for i in range(n)]


def probe(ip, timeout=5):
    try:
        with urllib.request.urlopen("http://%s:8790/health" % ip, timeout=timeout) as r:
            d = json.load(r)
        return {"up": True, "node": d.get("node"), "version": d.get("version")}
    except Exception as e:
        return {"up": False, "err": str(e)[:60]}


def machines():
    out = {}
    try:
        rv = json.load(open(os.path.join(STATE, "executor-revive.json"), encoding="utf-8"))
    except Exception:
        rv = {}
    for nid, ip in NODES.items():
        p = probe(ip)
        d = rv.get(nid) or {}
        v = str(d.get("verdict") or d.get("action") or "未探")
        try:
            age_h = (time.time() - float(d.get("ts"))) / 3600.0
        except Exception:
            age_h = None
        stale = v == "healthy" and age_h is not None and age_h > 1
        out[nid] = {"probe_up": p["up"], "verdict": v + ("·陈旧" if stale else ""),
                    "age_h": round(age_h, 1) if age_h is not None else None}
    return out


def queues():
    out = {}
    for st in SHARDS:
        p = os.path.join(ROOT, "cph4", "fleet", "rt", st, "queue.jsonl")
        try:
            rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        except Exception:
            continue
        out[st] = dict(collections.Counter(str(r.get("state")) for r in rows))
    return out


def output_stats():
    ds = days(8)
    per_day = {d: {"deliver": 0, "flow": 0} for d in ds}
    blocked_reasons = collections.Counter()
    for st in ("", ) + SHARDS:
        p = (os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl") if st == ""
             else os.path.join(ROOT, "cph4", "fleet", "rt", st, "queue.jsonl"))
        try:
            rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        except Exception:
            continue
        for r in rows:
            cid = str(r.get("id") or "")
            t = str(r.get("done_at") or r.get("finished_at") or r.get("ts") or "")[:10]
            if str(r.get("state")) == "DONE" and t in per_day:
                k = "flow" if any(m in cid.upper() for m in META) else "deliver"
                per_day[t][k] += 1
            if str(r.get("state")) == "BLOCKED":
                w = str(r.get("why") or "")
                if "命令" in w or "cmd" in w.lower():
                    blocked_reasons["命令未接"] += 1
                elif "产物" in w:
                    blocked_reasons["缺产物"] += 1
                elif "离线" in w or "不在线" in w:
                    blocked_reasons["机器离线"] += 1
                elif "工序表" in w:
                    blocked_reasons["工序表依赖"] += 1
                else:
                    blocked_reasons["其他"] += 1
    return per_day, blocked_reasons


def model_health():
    r = {"up": False}
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as f:
            d = json.load(f)
        r["up"] = True
        r["models"] = len(d.get("models") or [])
    except Exception as e:
        r["err"] = str(e)[:60]
    r["version"] = None
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=5) as f:
            r["version"] = json.load(f).get("version")
    except Exception:
        pass
    # 真跑一次短推理（只看能否出字，不做性能判定）
    try:
        body = json.dumps({"model": "qwen3.5:4b-mlx", "prompt": "回复两个字：正常",
                           "stream": False, "think": False,
                           "options": {"num_ctx": 1024, "temperature": 0},
                           "keep_alive": "1m"}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", body,
                                     {"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as f:
            d = json.load(f)
        ec = d.get("eval_count", 0)
        ed = (d.get("eval_duration") or 1) / 1e9
        r["tok_s"] = round(ec / ed, 1) if ed else None
        r["sample"] = (d.get("response") or "").strip()[:20]
        r["elapsed_s"] = round(time.time() - t0, 1)
    except Exception as e:
        r["run_err"] = str(e)[:60]
    return r


def silent_boundary():
    sentinel = os.path.exists(os.path.join(ROOT, ".codely-cli", "state", "FLEET-PAUSED"))
    import glob
    n = len(glob.glob(os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.*.plist")))
    va = None
    try:
        va = json.load(open(os.path.join(STATE, "viz-audit.json"), encoding="utf-8")).get("verdict")
    except Exception:
        pass
    return {"paused": sentinel, "autostart": n, "viz": va}


def build():
    per_day, reasons = output_stats()
    ds = days(8)
    today, yday = ds[0], ds[1]
    week = ds[:7]
    snap = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "day": today,
        "machines": machines(),
        "queues": queues(),
        "output": {
            "today": per_day[today], "yesterday": per_day[yday],
            "week_deliver": sum(per_day[d]["deliver"] for d in week),
            "week_flow": sum(per_day[d]["flow"] for d in week),
            "by_day": per_day,
        },
        "blocked_reasons": dict(reasons),
        "model": model_health(),
        "silent": silent_boundary(),
    }
    return snap


def render(s):
    m = s["machines"]
    q = s["queues"]
    o = s["output"]
    md = model = s["model"]
    sl = s["silent"]
    lines = ["# 全年巡查 · %s" % s["day"], "",
             "**今日交付 %d 张 / 流程 %d 张** · 昨日交付 %d · 近七日交付合计 %d"
             % (o["today"]["deliver"], o["today"]["flow"],
                o["yesterday"]["deliver"], o["week_deliver"]), ""]

    lines += ["## 一、机器", "", "| 机器 | 8790 | 执行器判定 | 判定龄 |", "|---|---|---|---|"]
    for k, v in m.items():
        lines.append("| %s | %s | %s | %s |" % (
            k, "在" if v["probe_up"] else "不通", v["verdict"],
            ("%.1fh" % v["age_h"]) if v["age_h"] is not None else "-"))
    up = sum(1 for v in m.values() if v["probe_up"])
    lines += ["", "可达 %d / %d 台。" % (up, len(m)), ""]

    lines += ["## 二、队列", "", "| 工位 | OPEN | RUNNING | BLOCKED | FAILED |", "|---|---|---|---|---|"]
    for k, v in q.items():
        lines.append("| %s | %s | %s | %s | %s |" % (
            k, v.get("OPEN", 0), v.get("RUNNING", 0), v.get("BLOCKED", 0), v.get("FAILED", 0)))
    lines += [""]

    lines += ["## 三、阻塞原因", ""]
    if s["blocked_reasons"]:
        for k, v in sorted(s["blocked_reasons"].items(), key=lambda x: -x[1]):
            lines.append("- %s：%d 张" % (k, v))
    else:
        lines.append("- 无")
    lines += [""]

    lines += ["## 四、本地模型", ""]
    if md.get("up"):
        lines.append("- ollama %s · %s 个模型 · 真跑 %s tok/s（%.1fs）· 回复「%s」"
                     % (md.get("version") or "-", md.get("models", "-"),
                        md.get("tok_s", "-"), md.get("elapsed_s", 0), md.get("sample") or "-"))
    else:
        lines.append("- **不可用**：%s" % md.get("err") or md.get("run_err"))
    lines += [""]

    lines += ["## 五、静默与看板", "",
              "- 静默边界：%s · 自启 %d 项 · 看板体检 %s"
              % ("已上锁" if sl["paused"] else "未上锁", sl["autostart"], sl["viz"] or "-"), ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--daily", action="store_true",
                    help="今天已生成过就直接返回（供主控脉每轮调用）")
    a = ap.parse_args()
    if a.daily:
        # 每轮被脉调用，但一天只真跑一次：已生成过今天就直接退出（0.01s）。
        try:
            if json.load(open(OUT_JS, encoding="utf-8")).get("day") == time.strftime("%Y-%m-%d"):
                return 0
        except Exception:
            pass
    s = build()
    md = render(s)
    print(md)
    if a.check:
        return 0
    os.makedirs(STATE, exist_ok=True)
    try:
        json.dump(s, open(OUT_JS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(OUT_MD, "w", encoding="utf-8").write(md + "\n")
        with open(HIST, "a", encoding="utf-8") as f:
            f.write(json.dumps({k: s[k] for k in ("ts", "day", "output",
                                                  "blocked_reasons")},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    bad = (not s["model"].get("up")) or sum(1 for v in s["machines"].values() if not v["probe_up"]) >= 2
    return 2 if bad else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
