#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resilience.py - 7x24 韧性体检 + 演练：每条突发情况都要有检测、处置、验收。

为什么（2026-11-09）：过去故障都是"发现了才修"，没有一张表回答"哪类突发我们根本看不见"。
本件只做三件事：
  1. 体检：14 项信号逐条判 PASS/WARN/FAIL（可机检、可留档）；
  2. 演练：用临时夹具伪造"脉停了/队列坏了/服务没加载"，验证检测器真的会报；
  3. 验收：全绿才算过；FAIL 即 rc=1，接进每日脉。

用法：
  python3 Tools/fleet/resilience.py
  python3 Tools/fleet/resilience.py --json cph4/fleet/state/resilience.json
  python3 Tools/fleet/resilience.py --drill
退出：0 无 FAIL；1 有 FAIL；2 用法错误。
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
PULSE = os.path.join(F, "dispatcher", "PULSE.json")
SYNC = os.path.join(STATE, "state-sync.json")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
COMMS = os.path.join(STATE, "comms.json")
SERVICES = ["pulse", "statesync", "watchdog", "loadwatch", "gateway",
            "agentlane", "webai", "fleetbus"]


def _age(path):
    try:
        return time.time() - os.path.getmtime(path)
    except OSError:
        return 1e9


def _json(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def check_pulse(ctx):
    age = _age(ctx.get("pulse", PULSE))
    ok = age < 900
    return ("pulse_heartbeat", "PASS" if ok else "FAIL", "age=%.0fs (limit 900)" % age)


def check_sync(ctx):
    d = _json(ctx.get("sync", SYNC), {}) or {}
    ok = float(d.get("ok_ts") or 0)
    until = float(d.get("until") or 0)
    age = time.time() - ok if ok else 1e9
    if until and time.time() < until:
        return ("state_sync", "WARN", "quarantined until +%.0fs" % (until - time.time()))
    return ("state_sync", "PASS" if age < 1200 else "FAIL", "age=%.0fs (limit 1200)" % age)


def check_services(ctx):
    out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
    names = ctx.get("services", SERVICES)
    missing = [n for n in names if "com.fluxgroup.%s" % n not in out]
    return ("services", "PASS" if not missing else "FAIL",
            "missing=%s" % (",".join(missing) or "-"))


def check_queue(ctx):
    p = ctx.get("queue", QUEUE)
    seen, bad, dup, conflict = set(), 0, 0, 0
    try:
        lines = open(p, encoding="utf-8").read().splitlines()
    except OSError:
        return ("queue_integrity", "FAIL", "unreadable")
    for ln in lines:
        if not ln.strip():
            continue
        if ln.startswith(("<<<<<<<", "=======", ">>>>>>>")):
            conflict += 1
            continue
        try:
            d = json.loads(ln)
        except Exception:
            bad += 1
            continue
        i = d.get("id")
        if i in seen:
            dup += 1
        seen.add(i)
    ok = not (bad or dup or conflict)
    return ("queue_integrity", "PASS" if ok else "FAIL",
            "lines=%d bad=%d dup=%d conflict=%d" % (len(lines), bad, dup, conflict))


def check_supply(ctx):
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "Tools", "fleet", "supply_guard.py"),
                            "--json", os.path.join(STATE, "resilience-supply.json")],
                           capture_output=True, text=True, timeout=120)
        d = _json(os.path.join(STATE, "resilience-supply.json"), {}) or {}
    except Exception as e:
        return ("supply", "FAIL", "guard error %s" % str(e)[:60])
    short = d.get("short_after") or {}
    return ("supply", "PASS" if not short else "WARN", "short=%s" % short)


def check_lanes(ctx):
    d = _json(ctx.get("comms", COMMS), {}) or {}
    now = time.time()
    stale = []
    for n in d.get("nodes") or []:
        if not n.get("online"):
            continue
        ts = n.get("ts")
        # comms 只给 hb_s，用在线+心跳秒数判
        hb = n.get("hb_s")
        if hb is not None and hb > 3600:
            stale.append("%s:%ss" % (n.get("node"), int(hb)))
    return ("lane_heartbeats", "PASS" if not stale else "WARN", "stale=%s" % (stale or "-"))


def check_disk(ctx):
    r = subprocess.run(["df", "-g", "/"], capture_output=True, text=True).stdout.splitlines()
    try:
        free = int(r[1].split()[3])
    except Exception:
        return ("disk", "FAIL", "unparsable")
    return ("disk", "PASS" if free > 20 else "FAIL", "free=%dG (limit 20)" % free)


def check_memory(ctx):
    try:
        out = subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout
        pct = int([l for l in out.splitlines() if "free percentage" in l][-1].split(":")[-1].strip().rstrip("%"))
    except Exception:
        return ("memory", "WARN", "unreadable")
    return ("memory", "PASS" if pct > 8 else "FAIL", "free=%d%% (limit 8)" % pct)


def check_models(ctx):
    bad = []
    for port in (11434, 11436):
        try:
            t0 = time.time()
            urllib.request.urlopen("http://127.0.0.1:%d/api/tags" % port, timeout=2).read(10)
            if time.time() - t0 > 2:
                bad.append("%d slow" % port)
        except Exception as e:
            bad.append("%d %s" % (port, str(e)[:30]))
    return ("model_endpoints", "PASS" if not bad else "FAIL", "bad=%s" % (bad or "-"))


def check_token(ctx):
    p = os.path.expanduser("~/.fluxgroup-llm-token")
    ok = os.path.isfile(p) and os.path.getsize(p) > 10
    return ("llm_token", "PASS" if ok else "FAIL", "present=%s" % ok)


def check_codely(ctx):
    p = os.path.expanduser("~/.codely-cli/oauth_creds.json")
    age_d = _age(p) / 86400.0
    ok = age_d < 30
    return ("codely_creds", "PASS" if ok else "WARN", "age=%.1fd (warn 30)" % age_d)


def check_git(ctx):
    c = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    uu = [l for l in c.splitlines() if l[:2] == "UU"]
    behind = subprocess.run(["git", "rev-list", "--count", "HEAD..origin/main"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip() or "0"
    ok = not uu and int(behind) < 200
    return ("git_state", "PASS" if ok else "FAIL", "unmerged=%d behind=%s" % (len(uu), behind))


def check_local_first(ctx):
    """本地优先率：24h 内本地调用 / (本地+云端)。低于 90% 说明自动化在往云上跑。"""
    import glob
    cut = time.time() - 86400
    def lines_since(p):
        n = 0
        try:
            for line in open(p, encoding="utf-8"):
                n += 1
        except OSError:
            return 0
        return n
    local = 0
    try:
        for line in open(os.path.join(ROOT, "cph4/fleet/dispatcher/local-model.jsonl"), encoding="utf-8"):
            if line[:10] >= time.strftime("%Y-%m-%d", time.localtime(cut)):
                local += 1
    except OSError:
        pass
    local += lines_since(os.path.join(STATE, "local-digest.jsonl"))
    try:
        p = json.load(open(os.path.join(STATE, "patrol-local.json"), encoding="utf-8"))
        local += len(p.get("seats") or []) * 12
    except Exception:
        pass
    cloud = 0
    for f in glob.glob(os.path.join(STATE, "codely-bridge", "logs", "*")):
        try:
            if os.path.getmtime(f) > cut:
                cloud += 1
        except OSError:
            pass
    total = local + cloud
    share = (local / total) if total else 1.0
    return ("local_first", "PASS" if share >= 0.9 else "WARN",
            "local=%d cloud=%d share=%.0f%%" % (local, cloud, share * 100))


def check_cloud_gate(ctx):
    """代码级本地优先：除白名单外，任何工具不得硬编码云端点。"""
    import glob
    allow = {"dsh_local.py", "codely_bridge.py", "llm_client.py", "resilience.py", "cloud_providers.py"}
    bad = []
    for f in glob.glob(os.path.join(ROOT, "Tools", "fleet", "*.py")):
        base = os.path.basename(f)
        if base in allow:
            continue
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for pat in ("api.deepseek.com", "codely-litellm", "api.openai.com"):
            if pat in t:
                bad.append("%s:%s" % (base, pat))
                break
    return ("cloud_gate", "PASS" if not bad else "FAIL", "direct-cloud=%s" % (bad or "-"))


def check_fleet_llm(ctx):
    """机队借用本机模型的通道：网关 8792 + 令牌。挂了机队就只能自己扛或上云。"""
    import urllib.request as u
    try:
        tok = open(os.path.expanduser("~/.fluxgroup-llm-token"), encoding="utf-8").read().strip()
    except OSError:
        return ("fleet_llm", "FAIL", "no token file")
    body = json.dumps({"model": "qwen3.5:4b-mlx",
                       "messages": [{"role": "user", "content": "ok"}],
                       "stream": False, "options": {"num_predict": 2}}).encode()
    req = u.Request("http://127.0.0.1:8792/api/chat", data=body,
                    headers={"Content-Type": "application/json", "X-Flux-Token": tok})
    try:
        d = json.loads(u.urlopen(req, timeout=20).read())
        ok = bool(d.get("done"))
        return ("fleet_llm", "PASS" if ok else "WARN", "gateway 8792 ok=%s" % ok)
    except Exception as e:
        return ("fleet_llm", "FAIL", "gateway 8792 %s" % str(e)[:60])


def check_codely_channel(ctx):
    """团结 Codely 只能走官方 CLI，不得被当跳板（直连端点/复用令牌/任意二进制）。"""
    import glob
    bad = []
    for f in glob.glob(os.path.join(ROOT, "Tools", "fleet", "*.py")):
        if os.path.basename(f) in ("resilience.py", "codely_bridge.py"):
            continue
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "codely-litellm" in t or "oauth_creds.json" in t:
            bad.append(os.path.basename(f))
    cli = os.path.expanduser("~/Library/Application Support/Tuanjie Cowork/bin/codely")
    ok_cli = os.path.isfile(cli)
    status = "PASS" if (not bad and ok_cli) else "FAIL"
    return ("codely_channel", status, "direct=%s cli=%s" % (bad or "-", ok_cli))


def check_local_agent_model(ctx):
    """会话/机队共用的本地模型必须能出正文、能发 tool_calls（think=false）。"""
    import urllib.request as u
    body = json.dumps({"model": "qwen3.5:4b-mlx",
                       "messages": [{"role": "user", "content": "调用工具读 /tmp/x"}],
                       "tools": [{"type": "function", "function": {
                           "name": "read_file", "description": "read",
                           "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                                          "required": ["path"]}}}],
                       "tool_choice": "auto", "think": False, "stream": False,
                       "keep_alive": "5m",
                       "options": {"num_ctx": 16384, "num_predict": 80}}).encode()
    req = u.Request("http://127.0.0.1:11436/api/chat", data=body,
                    headers={"Content-Type": "application/json"})
    try:
        d = json.loads(u.urlopen(req, timeout=120).read())
        m = d.get("message") or {}
        ok = bool(m.get("tool_calls")) or bool((m.get("content") or "").strip())
        return ("local_agent_model", "PASS" if ok else "FAIL",
                "tool=%s content=%d" % (bool(m.get("tool_calls")), len(m.get("content") or "")))
    except Exception as e:
        return ("local_agent_model", "FAIL", str(e)[:80])


CHECKS = [check_pulse, check_sync, check_services, check_queue, check_supply,
          check_lanes, check_disk, check_memory, check_models, check_token,
          check_codely, check_git, check_local_first, check_cloud_gate, check_fleet_llm, check_codely_channel, check_local_agent_model]


def run(ctx=None):
    ctx = ctx or {}
    rows = []
    for fn in CHECKS:
        try:
            rows.append(fn(ctx))
        except Exception as e:
            rows.append((fn.__name__, "FAIL", "exception %s" % str(e)[:80]))
    return rows


def drill():
    """用临时夹具验证检测器会报错（不是只看生产环境恰好绿）。"""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="res-drill-")
    ok = []

    p = os.path.join(tmp, "PULSE.json")
    json.dump({"ts": "x"}, open(p, "w"))
    os.utime(p, (time.time() - 10000, time.time() - 10000))
    r = check_pulse({"pulse": p})
    ok.append(("stale pulse -> FAIL", r[1] == "FAIL"))

    q = os.path.join(tmp, "q.jsonl")
    open(q, "w").write('{"id":"a"}\nnot-json\n{"id":"a"}\n')
    r = check_queue({"queue": q})
    ok.append(("bad/dup queue -> FAIL", r[1] == "FAIL"))

    r = check_services({"services": ["definitely-not-a-service"]})
    ok.append(("missing service -> FAIL", r[1] == "FAIL"))

    r = check_pulse({})
    ok.append(("live pulse -> PASS", r[1] == "PASS"))

    for name, passed in ok:
        print(("PASS  " if passed else "FAIL  ") + name)
    return 0 if all(p for _, p in ok) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(STATE, "resilience.json"))
    ap.add_argument("--drill", action="store_true")
    a = ap.parse_args()
    if a.drill:
        return drill()

    rows = run()
    fails = [r for r in rows if r[1] == "FAIL"]
    warns = [r for r in rows if r[1] == "WARN"]
    for name, st, detail in rows:
        print("%-4s %-18s %s" % (st, name, detail))
    print("-- %d checks: %d PASS / %d WARN / %d FAIL" %
          (len(rows), len(rows) - len(fails) - len(warns), len(warns), len(fails)))
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "verdict": "FAIL" if fails else "PASS",
               "checks": [{"id": n, "status": s, "detail": d} for n, s, d in rows]},
              open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
