#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_alloc.py - 算力调度器：有活即热、无活即卸、压力即止、无活不造。

CEO 2026-11-11：「把算力用到极致，合理用和分配，不能闲着还常驻」。

四条判据（都要可核验，不靠感觉）：
  1) 无活即卸   模型常驻但 N 分钟没调用 → 卸掉（keep_alive=0）。4B 重载约 0.4s，
                用 0.4s 换回几个 G 内存，比常驻划算。
  2) 有活即热   队列里真有要跑模型的卡 → 先预热对应座位，别让第一个请求吃冷启动。
  3) 压力即止   swap 已有增量或本机 hold 未释放 → 不预热、不接新活，排队等。
  4) 无活不造   队列空就如实报 NO-SUPPLY，不许为了"看起来在跑"编活。

用法：
  python3 Tools/fleet/compute_alloc.py status          # 一份账：谁常驻、占多久、利用率、有无可跑的活
  python3 Tools/fleet/compute_alloc.py reap --apply    # 真卸（默认 dry-run）
  python3 Tools/fleet/compute_alloc.py warm --seat big # 预热某座位（带预期工作时长）
  python3 Tools/fleet/compute_alloc.py alloc           # 分机分座的分配建议（不执行）
  python3 Tools/fleet/compute_alloc.py --self-test
Exit: 0 正常；1 判据不过；2 环境异常
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
AUDIT = os.path.join(FLEET, "dispatcher", "local-model.jsonl")
OUT = os.path.join(STATE, "compute-alloc.json")
LOCAL = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
IDLE_REAP_MIN = 10
UTIL_WINDOW_H = 24


# ---------------------------------------------------------------- 探针

def _get(url, path, timeout=3):
    with urllib.request.urlopen(url + path, timeout=timeout) as r:
        return json.loads(r.read())


def _post(url, path, payload, timeout=20):
    req = urllib.request.Request(url + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def loaded(url=None):
    try:
        return _get(url or LOCAL, "/api/ps").get("models") or []
    except Exception:
        return []


def audit_rows(limit=4000):
    rows = []
    try:
        with open(AUDIT, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
    except Exception:
        return []
    return rows[-limit:]


def _ts(s):
    try:
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0


def utilization(rows, hours=UTIL_WINDOW_H, now=None):
    """占空比 = 模型实际在算的秒数 ÷ 墙钟。分两个口径：整窗 / 活跃时段。"""
    now = now or time.time()
    lo = now - hours * 3600
    win = [r for r in rows if _ts(r.get("ts")) >= lo and r.get("op") in ("generate", "embed")
           and not r.get("err")]
    secs = sum(float(r.get("sec") or 0) for r in win)
    span = hours * 3600.0
    if win:
        span = max(60.0, now - _ts(win[0].get("ts")))
    return {"calls": len(win), "model_seconds": round(secs, 1),
            "window_s": int(span),
            "duty_pct": round(secs / span * 100, 2) if span else 0.0,
            "last_ts": win[-1].get("ts") if win else None}


def _norm(name):
    """Ollama 别名归一：qwen3.5:4b-mlx 与 qwen3.5:4b 是同一份权重（本机实测如此）。
    不归一的话 /api/ps 的名字在审计里找不到，闲置判定恒为"无记录"→ 永不卸载。"""
    if not name or ":" not in name:
        return name or ""
    repo, tag = name.split(":", 1)
    return repo + ":" + tag.split("-")[0]


def last_call_per_model(rows):
    out = {}
    for r in rows:
        m = r.get("model")
        if m and not r.get("err"):
            ts = _ts(r.get("ts"))
            out[m] = max(out.get(m, 0.0), ts)
            out[_norm(m)] = max(out.get(_norm(m), 0.0), ts)
    return out


def hold_active():
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
        import local_model as lm
        ok, info = lm.hold_active()
        return ok, info
    except Exception:
        return False, {}


def supply(root=None):
    """真实供给：分片里有多少卡能跑（OPEN + 有 cmd + 有产物契约）。"""
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    try:
        import station_shards as ss
        data = ss.load_all(root=root, prefer_remote=False)
    except Exception as e:
        return {"error": str(e)[:120], "runnable": 0, "open": 0, "need_cmd": 0}
    open_n = runnable = need_cmd = 0
    for _station, rows in (data or {}).items():
        for r in rows or []:
            if (r.get("state") or "").upper() != "OPEN":
                continue
            open_n += 1
            if (r.get("cmd") or "").strip():
                runnable += 1
            else:
                need_cmd += 1
    return {"open": open_n, "runnable": runnable, "need_cmd": need_cmd}


def seat_model(seat):
    try:
        with open(os.path.join(FLEET, "LOCAL-MODEL-POLICY.json"), encoding="utf-8-sig") as f:
            d = (json.load(f).get("duties") or {}).get(seat) or {}
        return d.get("model"), d.get("num_ctx") or 8192
    except Exception:
        return None, 8192


# ---------------------------------------------------------------- 三件事

def status(url=None):
    url = url or LOCAL
    rows = audit_rows()
    now = time.time()
    ps = loaded(url)
    last = last_call_per_model(rows)
    util = utilization(rows)
    hold_ok, hold_info = hold_active()
    sup = supply()

    resident = []
    waste_gb_min = 0.0
    for m in ps:
        name = m.get("name") or m.get("model")
        size_gb = round((m.get("size") or 0) / 1e9, 2)
        lc = last.get(name) or last.get(_norm(name))
        idle_min = round((now - lc) / 60, 1) if lc else None
        exp = m.get("expires_at")
        resident.append({"model": name, "size_gb": size_gb,
                         "idle_min": idle_min, "expires_at": exp})
        if idle_min is not None and idle_min > 1:
            waste_gb_min += size_gb * (idle_min - 1)

    verdict = "BALANCED"
    if resident and all((r["idle_min"] or 0) > IDLE_REAP_MIN for r in resident):
        verdict = "IDLE-REAP"          # 常驻却闲着：不科学
    elif sup.get("runnable", 0) > 0 and (not resident or util["duty_pct"] < 5):
        verdict = "WARM-AND-RUN"       # 有活却冷着：也不科学
    elif sup.get("open", 0) == 0:
        verdict = "NO-SUPPLY"          # 无活可干：如实说，不造活

    return {"ts": datetime.now().isoformat(timespec="seconds"), "endpoint": url,
            "resident": resident, "waste_gb_min": round(waste_gb_min, 1),
            "utilization": util, "hold": {"active": hold_ok, "info": hold_info},
            "supply": sup, "verdict": verdict, "idle_reap_min": IDLE_REAP_MIN}


def _is_mlx(model):
    """MLX 别名（/api/ps 报 qwen3.5:4b，策略里写 4b-mlx）→ 卸法必须换：
    LOCAL-MODEL-POLICY._keep_alive_why 记着实测——MLX runner 对 keep_alive=0
    会卡在 Stopping 且再也加载不上。卸错等于把模型弄坏。"""
    if "mlx" in (model or "").lower():
        return True
    try:
        with open(os.path.join(FLEET, "LOCAL-MODEL-POLICY.json"), encoding="utf-8-sig") as f:
            duties = json.load(f).get("duties") or {}
        for d in duties.values():
            if isinstance(d, dict):
                m = d.get("model") or ""
                if "mlx" in m.lower() and _norm(m) == _norm(model):
                    return True
    except Exception:
        pass
    return False


def _unload_value(model):
    return "1m" if _is_mlx(model) else 0


def reap(apply=False, idle_min=IDLE_REAP_MIN, url=None):
    url = url or LOCAL
    st = status(url)
    hold_ok, _ = hold_active()
    plan, done = [], []
    for r in st["resident"]:
        idle = r["idle_min"]
        if idle is None:
            plan.append({"model": r["model"], "action": "keep", "why": "无调用记录，保守不动"})
            continue
        if idle < idle_min:
            plan.append({"model": r["model"], "action": "keep",
                         "why": "闲置 %.1f 分钟 < %d" % (idle, idle_min)})
        elif hold_ok:
            plan.append({"model": r["model"], "action": "keep", "why": "本机 hold 未释放"})
        else:
            val = _unload_value(r["model"])
            plan.append({"model": r["model"], "action": "unload",
                         "why": "闲置 %.1f 分钟，占 %.2fG（keep_alive=%s）"
                                % (idle, r["size_gb"], val),
                         "keep_alive": val})
            if apply:
                try:
                    _post(url, "/api/generate", {"model": r["model"], "keep_alive": val}, 30)
                    done.append(r["model"])
                except Exception as e:
                    done.append("%s(失败:%s)" % (r["model"], str(e)[:60]))
    return {"dry_run": not apply, "plan": plan, "unloaded": done, "verdict": st["verdict"]}


def warm(seat="big", minutes=10, url=None, apply=False):
    """有活才预热：无供给直接拒绝，避免"闲着还常驻"的另一种形态。"""
    url = url or LOCAL
    sup = supply()
    if sup.get("runnable", 0) == 0:
        return {"ok": False, "why": "NO-SUPPLY：分片里没有带 cmd 的可跑卡，不预热",
                "supply": sup}
    hold_ok, _ = hold_active()
    if hold_ok:
        return {"ok": False, "why": "本机 hold 未释放，排队等", "supply": sup}
    model, ctx = seat_model(seat)
    if not model:
        return {"ok": False, "why": "座位 %s 未在 LOCAL-MODEL-POLICY 定义" % seat, "supply": sup}
    if not apply:
        return {"ok": True, "dry_run": True, "model": model, "keep_alive": "%dm" % minutes,
                "num_ctx": ctx, "supply": sup}
    t0 = time.time()
    try:
        _post(url, "/api/generate", {"model": model, "prompt": "预热", "stream": False,
                                     "think": False, "keep_alive": "%dm" % minutes,
                                     "options": {"num_predict": 1, "num_ctx": ctx}}, 120)
        return {"ok": True, "model": model, "load_s": round(time.time() - t0, 2),
                "keep_alive": "%dm" % minutes, "supply": sup}
    except Exception as e:
        return {"ok": False, "why": str(e)[:120], "supply": sup}


def alloc(rows=None):
    """分机分配建议：按每机预算与供给，给出"谁该接什么"，只算不执行。"""
    try:
        with open(os.path.join(FLEET, "AGENT-CAPACITY-v1.json"), encoding="utf-8") as f:
            cap = json.load(f)
    except Exception:
        cap = {}
    try:
        with open(os.path.join(FLEET, "STATIONS.json"), encoding="utf-8") as f:
            st = json.load(f).get("stations") or []
    except Exception:
        st = []
    sup = supply()
    machines = cap.get("machines") or {}
    out = []
    for m in st:
        mid = m.get("id")
        c = machines.get(mid) or {}
        out.append({
            "station": mid, "name": m.get("name") or c.get("name"),
            "model": (m.get("local_model") or {}).get("model") or c.get("model"),
            "budget_calls_per_day": (c.get("budget") or {}).get("calls_per_day"),
            "concurrency": c.get("concurrency"),
            "take": "先吃自己的活" if sup.get("runnable", 0) else "无活，保持卸载",
        })
    brain_local = (machines.get("brain") or {})
    return {"supply": sup, "stations": out,
            "brain": {"tok_s_assumed": brain_local.get("tok_s"),
                      "budget_calls": (brain_local.get("budget") or {}).get("calls_per_day"),
                      "note": "大脑未入网前一律回落本机；入网后深席改指它，本机只做 triage+"}}


# ---------------------------------------------------------------- 自检

def self_test():
    global AUDIT
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    hits = {"unload": 0, "values": []}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            body = json.dumps({"models": [
                {"name": "qwen3.5:4b", "size": 4000000000,
                 "expires_at": "2026-11-11T17:00:00+08:00"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
            if "keep_alive" in d:
                hits["values"].append(d.get("keep_alive"))
                if str(d.get("keep_alive")) in ("0", "1m", "10s"):
                    hits["unload"] += 1
            body = b'{"response":"ok"}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d" % srv.server_address[1]

    ok = 0
    total = 0

    def chk(name, cond, detail=""):
        nonlocal ok, total
        total += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name,
                             "" if cond else "  <- " + str(detail)))

    # 1) 空账时占空比为 0，不报假忙
    u = utilization([], hours=1, now=time.time())
    chk("无调用记录 -> 占空比 0、调用 0", u["duty_pct"] == 0 and u["calls"] == 0, u)

    # 2) 占空比按真实 sec 算
    now = time.time()
    rows = [{"ts": datetime.fromtimestamp(now - 60).isoformat(), "op": "generate", "sec": 30},
            {"ts": datetime.fromtimestamp(now - 30).isoformat(), "op": "generate", "sec": 20}]
    u = utilization(rows, hours=1, now=now)
    chk("2 次 50s 模型时间 -> 占空比 >0 且 model_seconds=50",
        u["model_seconds"] == 50 and u["duty_pct"] > 0, u)

    # 3) 有常驻但无任何调用记录 -> 保守不动（不误卸）
    empty_audit = os.path.join(STATE, "compute-alloc-empty.jsonl")
    os.makedirs(STATE, exist_ok=True)
    open(empty_audit, "w").close()
    real_audit = AUDIT
    AUDIT = empty_audit
    r = reap(apply=False, url=url)
    chk("无调用记录的常驻模型保守不动", r["plan"] and r["plan"][0]["action"] == "keep", r)
    AUDIT = real_audit

    # 4) 有调用记录且闲置超阈值 -> 计划卸载；dry-run 不动手
    tmp = os.path.join(STATE, "compute-alloc-selftest.jsonl")
    os.makedirs(STATE, exist_ok=True)
    old = (now - 40 * 60)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.fromtimestamp(old).isoformat(), "op": "generate",
                            "sec": 1, "model": "qwen3.5:4b"}) + "\n")
    real_audit = AUDIT
    AUDIT = tmp
    r = reap(apply=False, url=url)
    chk("闲置 40 分钟 -> 计划 unload（dry-run 不真卸）",
        r["plan"] and r["plan"][0]["action"] == "unload" and hits["unload"] == 0, r)

    # 5) --apply 时才真卸；且 MLX 别名必须用 1m 而不是 0（0 会卡在 Stopping）
    r = reap(apply=True, url=url)
    chk("apply 才卸载（打一次 keep_alive）", hits["unload"] == 1 and r["unloaded"], r)
    chk("MLX 别名卸载用 1m 不用 0", hits["values"] and hits["values"][-1] == "1m", hits)

    # 6) 无供给时预热必须拒绝（不许无活常驻）
    real_supply = globals()["supply"]
    globals()["supply"] = lambda root=None: {"open": 0, "runnable": 0, "need_cmd": 0}
    w = warm(seat="big", apply=True, url=url)
    chk("无供给 -> 拒绝预热", w["ok"] is False and "NO-SUPPLY" in w["why"], w)

    # 7) 有供给但 hold 未释放 -> 排队不预热
    globals()["supply"] = lambda root=None: {"open": 1, "runnable": 1, "need_cmd": 0}
    real_hold = globals()["hold_active"]
    globals()["hold_active"] = lambda: (True, {"cls": "master"})
    w = warm(seat="big", apply=True, url=url)
    chk("hold 未释放 -> 排队", w["ok"] is False and "hold" in w["why"], w)

    # 8) 有供给且无 hold -> 预热用座位模型
    globals()["hold_active"] = lambda: (False, {})
    w = warm(seat="big", apply=True, url=url)
    chk("有供给 -> 预热到座位模型", w["ok"] is True and w.get("model"), w)

    # 9) 座位未定义要报错而不是瞎猜
    w = warm(seat="no-such-seat", apply=True, url=url)
    chk("未定义座位 -> 明确拒绝", w["ok"] is False and "未在" in w["why"], w)

    # 10) 策略里的 keep_alive=0 必须原样下发（假值被 or 吞掉=模型偷偷常驻）；
    #     顺带证 num_ctx 以策略为天花板（2026-11-14：签名默认 8192 曾把策略的 32768 压成 8192）
    import local_model as lm2
    cap = {}
    real = (lm2._post, lm2._audit, lm2.hold, lm2.release, lm2._duties)
    lm2._post = lambda path, payload, timeout: (cap.update(payload), {"response": "ok"})[1]
    lm2._audit = lambda row: None
    lm2.hold = lambda *a, **k: None
    lm2.release = lambda: None
    # 用合成策略断言代码行为，不绑生产策略文件的具体数值（绑了会因换档假红）
    lm2._duties = lambda: {"big": {"model": "fake:1b", "keep_alive": 0, "num_ctx": 32768}}
    lm2.generate("x", cls="review")
    chk("策略 keep_alive=0 原样下发（不被 or 吞）", cap.get("keep_alive") == 0, cap.get("keep_alive"))
    chk("未指定 num_ctx 时取策略值（默认不再压成 8192）",
        (cap.get("options") or {}).get("num_ctx") == 32768, (cap.get("options") or {}).get("num_ctx"))
    lm2.generate("x", cls="review", num_ctx=2048)
    chk("调用方要求更小的 num_ctx 时取更小",
        (cap.get("options") or {}).get("num_ctx") == 2048, (cap.get("options") or {}).get("num_ctx"))
    lm2._post, lm2._audit, lm2.hold, lm2.release, lm2._duties = real

    globals()["supply"] = real_supply
    globals()["hold_active"] = real_hold
    AUDIT = real_audit
    srv.shutdown()
    srv.server_close()
    print("[compute_alloc] %d/%d" % (ok, total))
    return 0 if ok == total else 1


# ---------------------------------------------------------------- 主流程

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="status",
                    choices=["status", "reap", "warm", "alloc"])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--seat", default="big")
    ap.add_argument("--minutes", type=int, default=10)
    ap.add_argument("--idle-min", type=int, default=IDLE_REAP_MIN)
    ap.add_argument("--url", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    if a.cmd == "status":
        st = status(a.url)
        print("端点 %s | 判读 %s" % (st["endpoint"], st["verdict"]))
        if st["resident"]:
            for r in st["resident"]:
                print("  常驻 %-22s %5.2fG  闲置 %s 分钟" % (r["model"], r["size_gb"], r["idle_min"]))
            print("  闲置浪费 ≈ %.1f GB·min" % st["waste_gb_min"])
        else:
            print("  常驻：无（模型已卸，内存归机队与 CEO 办公）")
        u = st["utilization"]
        print("  近 %dh：%d 次调用 / %.1f 秒模型时间 / 占空比 %.2f%%（活跃时段口径）"
              % (UTIL_WINDOW_H, u["calls"], u["model_seconds"], u["duty_pct"]))
        s = st["supply"]
        print("  供给：OPEN %s 张 / 有 cmd %s / 缺 cmd %s"
              % (s.get("open"), s.get("runnable"), s.get("need_cmd")))
    elif a.cmd == "reap":
        r = reap(apply=a.apply, idle_min=a.idle_min, url=a.url)
        for p in r["plan"]:
            print("  %-8s %-22s %s" % (p["action"], p["model"], p["why"]))
        print("  %s" % ("已卸：" + ",".join(r["unloaded"]) if r["unloaded"]
                        else ("dry-run，加 --apply 才真卸" if r["dry_run"] else "无需卸载")))
    elif a.cmd == "warm":
        w = warm(seat=a.seat, minutes=a.minutes, url=a.url, apply=a.apply)
        print(json.dumps(w, ensure_ascii=False, indent=1))
    elif a.cmd == "alloc":
        print(json.dumps(alloc(), ensure_ascii=False, indent=1))

    try:
        os.makedirs(STATE, exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds"),
                       "cmd": a.cmd, "status": status(a.url)}, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
