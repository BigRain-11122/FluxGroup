#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""router.py - one place that decides which model handles a piece of work.

Principle: judge first, model later. Deterministic code decides tier; every tier passes the
SAME verification gate (paths must exist, commands must be in the repo, banned claims out).
Cloud is not privileged - it only runs when it is explicitly allowed and a key exists.

Tiers
  code        nothing to ask a model (caller handles it)
  local       qwen3.5:4b, resident, ~4.2GB
  local-heavy qwen3.5:35b-a3b, loaded on demand only if mem_gate says OK
  cloud       opt-in via cloud_ok + API key + budget; audited like every other tier
  human       all tiers failed the gate -> NEEDS-HUMAN, never a made-up answer

Audit: one JSONL line per attempt in cph4/fleet/dispatcher/events.jsonl (same stream as
fleet events), so "how much cloud, how often rejected" is measurable, not asserted.
"""
import json, os, re, subprocess, sys, time, urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EVENTS = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "events.jsonl")
BUDGET = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "cloud-budget.json")
# 2026-11-08：local 档读策略单源（此前写死 qwen3.5:4b，而现役是 4b-mlx，两者是两个模型）
try:
    import local_model as _lm
    _RES = ((_lm._duties().get("resident") or {}).get("model") or "qwen3.5:4b-mlx")
    _SEALED = ((_lm._duties().get("sealed") or {}).get("model") or "qwen3.5:35b-a3b")
except Exception:
    _RES, _SEALED = "qwen3.5:4b-mlx", "qwen3.5:35b-a3b"
MODELS = {"local": _RES, "local-heavy": _SEALED}
CLOUD_MODEL = os.environ.get("ROUTER_CLOUD_MODEL", "deepseek-v4.1-flash")
DAILY_CAP = float(os.environ.get("ROUTER_DAILY_CAP", "200"))
PER_CALL = float(os.environ.get("ROUTER_PER_CALL_CAP", "50"))


def _audit(row):
    row["ts"] = datetime.now().isoformat(timespec="seconds")
    try:
        os.makedirs(os.path.dirname(EVENTS), exist_ok=True)
        with open(EVENTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _mem_ok(need_gb):
    try:
        out = subprocess.check_output([sys.executable, os.path.join(HERE, "mem_gate.py"),
                                       "--need-gb", str(need_gb), "--json"], text=True)
        return json.loads(out).get("verdict") in ("OK",)
    except Exception:
        return False


def _spend():
    try:
        d = json.load(open(BUDGET, encoding="utf-8"))
    except Exception:
        d = {}
    today = datetime.now().strftime("%Y%m%d")
    if d.get("date") != today:
        d = {"date": today, "spent": 0.0, "calls": 0}
    return d


def _charge(est):
    d = _spend()
    d["spent"] = round(float(d["spent"]) + float(est), 3)
    d["calls"] = int(d["calls"]) + 1
    json.dump(d, open(BUDGET, "w", encoding="utf-8"), ensure_ascii=False)
    return d


def gate(text, allowed_files):
    """Same gate for every tier: no invented paths, no banned claims."""
    problems = []
    cited = set(re.findall(r"[A-Za-z0-9_./-]+\.(?:md|json|py|txt)", text or ""))
    ghost = [c for c in cited if allowed_files and not any(c == a or c in a or a.endswith(c) for a in allowed_files)]
    if ghost:
        problems.append("ghost-path:" + ",".join(sorted(ghost)[:3]))
    for w in ("绝对", "全网第一", "零风险", "稳赚", "包过"):
        if w in (text or ""):
            problems.append("banned:" + w)
    return problems


def _gen(model, prompt, timeout=300):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "keep_alive": "5m",
                       "options": {"num_ctx": 8192, "temperature": 0.2}}).encode()
    t0 = time.time()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = (json.load(r).get("response") or "").strip()
    return txt, round(time.time() - t0, 1)


def ask(prompt, job="", allowed_files=None, cloud_ok=False, downstream=False):
    """Returns dict(text, tier, gate). Escalates local -> local-heavy -> cloud -> human."""
    # 周期件禁云：脉冲里跑的自动阶段一律不许上云（CEO 2026-11-02 令）。
    if cloud_ok and os.environ.get("FLUX_AUTOMATION") == "1":
        _audit({"kind": "route", "job": job, "tier": "cloud", "gate": "blocked",
                "why": "periodic automation may not use cloud"})
        cloud_ok = False
    for tier in ("local", "local-heavy"):
        if tier == "local-heavy" and not _mem_ok(22):
            _audit({"kind": "route-skip", "job": job, "tier": tier,
                    "why": "mem_gate says no room for 22GB"})
            continue
        try:
            txt, sec = _gen(MODELS[tier], prompt)
        except Exception as e:
            _audit({"kind": "route-error", "job": job, "tier": tier, "err": str(e)[:120]})
            continue
        probs = gate(txt, allowed_files)
        _audit({"kind": "route", "job": job, "tier": tier, "model": MODELS[tier],
                "latency_s": sec, "gate": "pass" if not probs else "reject:" + ",".join(probs)})
        if not probs:
            if tier == "local-heavy":
                try:
                    urllib.request.urlopen(urllib.request.Request(
                        "http://127.0.0.1:11434/api/generate",
                        data=json.dumps({"model": MODELS[tier], "keep_alive": 0}).encode(),
                        headers={"Content-Type": "application/json"}), timeout=60).read()
                except Exception:
                    pass
            return {"text": txt, "tier": tier, "gate": "pass"}

    key = os.environ.get("DEEPSEEK_API_KEY")
    d = _spend()
    if cloud_ok and downstream and key and (d["spent"] + PER_CALL) <= DAILY_CAP:
        _audit({"kind": "route", "job": job, "tier": "cloud", "model": CLOUD_MODEL,
                "gate": "skipped", "why": "cloud path configured but not exercised in this build"})
    _audit({"kind": "route", "job": job, "tier": "human", "gate": "exhausted"})
    return {"text": "", "tier": "human", "gate": "needs-human"}


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "用一句话说明机队主控的职责。"
    print(json.dumps(ask(p, job="cli"), ensure_ascii=False))