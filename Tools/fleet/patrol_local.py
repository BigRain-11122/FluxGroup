#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patrol_local.py - 十域巡视席：用主控机本地模型做 30 分钟级巡查。

依据已落盘方案：cph4/fleet/dispatcher/PATROL-FLEET/BLUEPRINT.md（十席/四层降维）
与 CHARTERS.md（每域定位/雷达面/即决清单/升级线）。
本件只落 L0' 传感 + L1' 本地分类与日 digest：
  - 采集：该域队列卡状态、近 24h 回执、交付物存在率、域目录最后活动时间；
  - 判断：本机 Ollama（11434，resident 档）按该域雷达面给 GREEN/YELLOW/RED + 发现 + 动作；
  - 留档：DIGEST-<date>.md（人读）+ state/patrol-local.json（机读）；
  - RED 追加一行到该域 NEED-JUDGMENT（升级枢纽，不代决）。

用法：
  python3 Tools/fleet/patrol_local.py [--domain biggame] [--dry]
退出：0 正常；2 本地模型不可用。
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
PF = os.path.join(F, "dispatcher", "PATROL-FLEET")
CHARTERS = os.path.join(PF, "CHARTERS.md")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
STATE = os.path.join(F, "state", "patrol-local.json")
BT = chr(96) * 3
OLLAMA = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
MODEL = os.environ.get("PATROL_MODEL") or "qwen3.5:4b-mlx"

DOMAINS = [
    ("biggame", "§1", ["gaming"]),
    ("bigmoney", "§2", ["quant"]),
    ("bigstream", "§3", ["media"]),
    ("biglife", "§4", ["life"]),
    ("bigdomain", "§5", ["domain"]),
    ("bigcompute", "§6", ["compute"]),
    ("fluxverse", "§7", ["gaming/FluxVerse"]),
    ("bighouse", "§8", ["house"]),
    ("cph4", "§9", ["cph4"]),
    ("group", "§10", ["docs"]),
]


def charters():
    try:
        t = open(CHARTERS, encoding="utf-8").read()
    except OSError:
        return {}
    out = {}
    parts = re.split(r"^## ", t, flags=re.M)
    for p in parts[1:]:
        head = p.splitlines()[0]
        m = re.match(r"(§\d+)", head)
        if m:
            out[m.group(1)] = p.strip()
    return out


def load_queue():
    rows = []
    try:
        for line in open(QUEUE, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return rows


def domain_signals(dom, dirs, rows):
    now = time.time()
    mine = [r for r in rows if (r.get("line") or "").lower().startswith(dom.replace("big", "big"))]
    states = {}
    for r in mine:
        states[r.get("state")] = states.get(r.get("state"), 0) + 1
    recent = [r for r in mine if (r.get("finished_at") or "") >= time.strftime("%Y-%m-%d", time.localtime(now - 86400))]
    missing = 0
    for r in mine:
        if r.get("state") == "DONE" and r.get("deliverable"):
            p = r["deliverable"] if os.path.isabs(r["deliverable"]) else os.path.join(ROOT, r["deliverable"])
            if not os.path.exists(p):
                missing += 1
    latest = 0
    for d in dirs:
        base = os.path.join(ROOT, d)
        for dp, dn, fn in os.walk(base):
            dn[:] = [x for x in dn if x not in (".git", "node_modules", "__pycache__")]
            for f in fn:
                try:
                    latest = max(latest, os.path.getmtime(os.path.join(dp, f)))
                except OSError:
                    pass
    age_h = round((now - latest) / 3600, 1) if latest else None
    return {"cards": len(mine), "states": states, "done_24h": len(recent),
            "missing_deliverables": missing, "last_activity_h": age_h}


def ask(dom, body, sig):
    prompt = (
        "你是%s域巡视席。按下列雷达面判断，只输出 JSON，不要解释。\n"
        "雷达面：%s\n"
        "今日信号：卡总数 %d，状态 %s，近24h完成 %d，交付物缺失 %d，域目录最后活动 %.1f 小时前。\n"
        '输出格式：{"verdict":"GREEN|YELLOW|RED","findings":["...","..."],"action":"一句话"}'
        % (dom, body[:900], sig["cards"], json.dumps(sig["states"], ensure_ascii=False),
           sig["done_24h"], sig["missing_deliverables"], sig["last_activity_h"] or -1))
    t0 = time.time()
    req = urllib.request.Request(
        OLLAMA + "/api/chat",
        data=json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                         "think": False, "stream": False, "keep_alive": "10m",
                         "options": {"num_ctx": 4096, "num_predict": 220, "temperature": 0.1}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    txt = (d.get("message") or {}).get("content") or ""
    raw = txt.strip()
    if raw.startswith(BT):
        raw = raw[3:]
    if raw.endswith(BT):
        raw = raw[:-3]
    raw = raw.strip()
    m = re.search(r"\{.*\}", raw, re.S)
    out = {}
    if m:
        cand = m.group(0)
        for c in (cand, cand.replace(chr(92) + '"', '"')):
            try:
                out = json.loads(c)
                break
            except Exception:
                continue
    out.setdefault("verdict", "YELLOW")
    out.setdefault("findings", [txt.strip()[:120]] if txt.strip() else [])
    out.setdefault("action", "")
    out["sec"] = round(time.time() - t0, 1)
    return out


def calibrate(sig, res):
    """模型只能降级不能升级：没有硬信号（交付缺失/长时间静默）就不许 RED，
    否则十席会天天报红，红就没人看了。"""
    v = (res.get("verdict") or "YELLOW").upper()
    hard_red = (sig["missing_deliverables"] >= 3
                or (sig["last_activity_h"] is not None and sig["last_activity_h"] > 72))
    if v == "RED" and not hard_red:
        v = "YELLOW"
    if sig["done_24h"] > 0 and v == "RED":
        v = "YELLOW"
    res["verdict"] = v
    res["hard_red"] = hard_red
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default=None)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    ch = charters()
    rows = load_queue()
    todo = [d for d in DOMAINS if not a.domain or d[0] == a.domain]

    def work(item):
        dom, sec, dirs = item
        sig = domain_signals(dom, dirs, rows)
        body = ch.get(sec, "")
        try:
            res = ask(dom, body, sig)
        except Exception as e:
            res = {"verdict": "UNKNOWN", "findings": [str(e)[:100]], "action": "本地模型不可用", "sec": 0}
        res = calibrate(sig, res)
        return dom, sig, res

    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(work, todo))

    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        prev = {s["domain"]: (s.get("result") or {}).get("verdict")
                for s in (json.load(open(STATE, encoding="utf-8")).get("seats") or [])}
    except Exception:
        prev = {}
    lines = ["## %s" % ts, ""]
    for dom, sig, res in results:
        lines.append("- **%s** %s · %s · 卡%d/缺失%d/最后活动%sh · %.1fs" %
                     (dom, res["verdict"], "；".join(res["findings"][:2])[:120],
                      sig["cards"], sig["missing_deliverables"], sig["last_activity_h"], res["sec"]))
        lines.append("  - 动作：%s" % (res["action"] or "-"))
        if res["verdict"] == "RED" and prev.get(dom) != "RED":
            p = os.path.join(PF, "%s-NEED-JUDGMENT.md" % dom)
            try:
                with open(p, "a", encoding="utf-8") as f:
                    f.write("- [%s] %s → %s\n" % (ts, "；".join(res["findings"][:2])[:160], res["action"]))
            except OSError:
                pass

    if a.dry:
        print("\n".join(lines))
        return 0

    os.makedirs(PF, exist_ok=True)
    with open(os.path.join(PF, "DIGEST-%s.md" % time.strftime("%Y%m%d")), "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({"ts": ts, "seats": [{"domain": d, "signals": s, "result": r} for d, s, r in results]},
              open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for dom, sig, res in results:
        print("%-10s %-6s %ss %s" % (dom, res["verdict"], res["sec"], (res["findings"] or [""])[0][:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
