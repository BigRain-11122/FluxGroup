#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brain_stress.py - 合理的压力测试：只验机制边界，不做重度生产。

CEO 2026-11-11：「压力测试要合理，不是让你重度生产」。所以三档都带硬上限：

  --mode ladder  端点阶梯 / 探活 / 退避 / 健康缓存（跑假端点，零模型成本，默认 <10s）
  --mode local   真模型小档并发（默认 1/2/4 各 2 次 + 1 次预热，prompt 极短）
  --mode plan    大脑容量与漫剧需求反推（纯算术，不碰网络）

硬闸（任一触发立即停，不再发请求）：
  swap 增量 > --max-swap-mb(300) / 单次调用 > --call-timeout(60)
  总调用数 > --max-calls(14) / 总时长 > --max-seconds(180)

用法：
  python3 Tools/fleet/brain_stress.py --mode all
  python3 Tools/fleet/brain_stress.py --mode ladder --verbose
  python3 Tools/fleet/brain_stress.py --mode local --levels 1,2
  python3 Tools/fleet/brain_stress.py --mode local --url http://<brain>:11434   # 入网当天复跑
产物：cph4/fleet/state/brain-stress.json
Exit: 0 全过；1 有一条判据没过；2 环境异常（端点不可达）
"""
import argparse
import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
OUT = os.path.join(STATE, "brain-stress.json")
DEFAULT_LOCAL = "http://127.0.0.1:11434"
LEVELS = [1, 2, 4]
PER_LEVEL = 2
MAX_CALLS = 14
MAX_SECONDS = 180
CALL_TIMEOUT = 60
MAX_SWAP_MB = 300.0


# ---------------------------------------------------------------- 硬闸

def swap_mb():
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                                 text=True, timeout=5).stdout
            return float(out.split("used =")[1].split("M")[0].strip())
        except Exception:
            return -1.0
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("SwapTotal"):
                    return 0.0
    except Exception:
        pass
    return -1.0


class Budget:
    """调用次数/时长/swap 三重闸；任何一次超限都让后续调用直接放弃。"""

    def __init__(self, max_calls, max_seconds, max_swap_mb, label=""):
        self.max_calls = max_calls
        self.max_seconds = max_seconds
        self.max_swap_mb = max_swap_mb
        self.t0 = time.time()
        self.calls = 0
        self.label = label
        self.swap0 = swap_mb()
        self.stop_reason = ""

    def check(self):
        if self.stop_reason:
            return False
        if self.calls >= self.max_calls:
            self.stop_reason = "max-calls=%d" % self.max_calls
        elif time.time() - self.t0 > self.max_seconds:
            self.stop_reason = "max-seconds=%d" % self.max_seconds
        else:
            now = swap_mb()
            if self.swap0 >= 0 and now >= 0 and now - self.swap0 > self.max_swap_mb:
                self.stop_reason = "swap+%.0fMB>%0.fMB" % (now - self.swap0, self.max_swap_mb)
        return not self.stop_reason

    def take(self):
        self.calls += 1

    def summary(self):
        return {"label": self.label, "calls": self.calls,
                "seconds": round(time.time() - self.t0, 1),
                "swap_delta_mb": round((swap_mb() - self.swap0), 1) if self.swap0 >= 0 else None,
                "stopped_by": self.stop_reason or None}


# ---------------------------------------------------------------- 假端点

def _stub(behavior="ok", delay=0.0):
    """behavior: ok | hang（仅 POST 挂） | hang-all（连探活也挂） | error。
    只监听 127.0.0.1，不对外。"""

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if behavior == "hang-all":
                time.sleep(delay or 6.0)
            if self.path.startswith("/api/tags"):
                self._json(200, {"models": []})
            else:
                self._json(404, {})

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(n)
            except Exception:
                pass
            if behavior == "hang":
                time.sleep(delay or 6.0)
                self._json(200, {"response": "late"})
            elif behavior == "error":
                self._json(500, {"error": "stub-500"})
            else:
                if delay:
                    time.sleep(delay)
                self._json(200, {"response": "ok", "eval_count": 8,
                                 "eval_duration": 200000000})

        def _json(self, code, obj):
            body = json.dumps(obj).encode()
            try:
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def _dead_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _patched_lm(gateways):
    """把 local_model 指向临时配置与临时审计，避免污染真账。"""
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import local_model as lm
    tmp = tempfile.mkdtemp(prefix="brain-stress-")
    cfg = os.path.join(tmp, "compute.json")
    with open(cfg, "w", encoding="utf-8") as f:
        json.dump({"gateways": gateways}, f)
    lm.URL = ""
    lm.COMPUTE = cfg
    lm.AUDIT = os.path.join(tmp, "audit.jsonl")
    lm.HOLD = os.path.join(tmp, "hold.json")
    lm._HEALTH = {"ts": 0.0, "url": ""}
    lm._BAD = {}
    return lm, tmp


# ---------------------------------------------------------------- 一、端点阶梯

def ladder(verbose=False, budget=None):
    """验四件事：选中顺序、死端点跳过、挂死端点被超时切走、健康缓存 30s 内不重探。"""
    budget = budget or Budget(MAX_CALLS, 60, MAX_SWAP_MB, "ladder")
    rows = []

    def rec(name, ok, expect, got, ms, note=""):
        rows.append({"case": name, "ok": bool(ok), "expect": expect,
                     "got": got, "ms": int(ms), "note": note})
        if verbose:
            print("  [%s] %-26s expect=%s got=%s %sms %s"
                  % ("PASS" if ok else "FAIL", name, expect, got, int(ms), note))

    # 1) 大脑活着且 order=1 → 必须选中大脑，而不是主控
    brain, bport = _stub("ok")
    ctl, cport = _stub("ok")
    lm, _ = _patched_lm([
        {"id": "brain", "order": 1, "url": "http://127.0.0.1:%d" % bport},
        {"id": "control", "order": 2, "url": "http://127.0.0.1:%d" % cport},
    ])
    t = time.time()
    got = lm.endpoint()
    rec("brain-up-wins", got.endswith(str(bport)), "brain:%d" % bport, got.split(":")[-1], (time.time() - t) * 1000)
    brain.shutdown(); brain.server_close(); ctl.shutdown(); ctl.server_close()

    # 2) 大脑整体挂死（连探活都不回）→ 必须在 1.2s 探活超时后切到主控
    brain, bport = _stub("hang-all", 6.0)
    ctl, cport = _stub("ok")
    lm, _ = _patched_lm([
        {"id": "brain", "order": 1, "url": "http://127.0.0.1:%d" % bport},
        {"id": "control", "order": 2, "url": "http://127.0.0.1:%d" % cport},
    ])
    t = time.time()
    got = lm.endpoint()
    ms = (time.time() - t) * 1000
    rec("brain-hang-falls-through", got.endswith(str(cport)) and ms < 3000,
        "control within 3000ms", "%s / %dms" % (got.split(":")[-1], int(ms)), ms)
    brain.shutdown(); brain.server_close(); ctl.shutdown(); ctl.server_close()

    # 2b) 标签活着但生成长挂（探活骗过判定）→ 必须降级它并换端点拿到结果
    brain, bport = _stub("hang", 4.0)
    ctl, cport = _stub("ok")
    lm, _ = _patched_lm([
        {"id": "brain", "order": 1, "url": "http://127.0.0.1:%d" % bport},
        {"id": "control", "order": 2, "url": "http://127.0.0.1:%d" % cport},
    ])
    t = time.time()
    out = lm.generate("ping", cls="probe", timeout=2, why="brain-stress")
    ms = (time.time() - t) * 1000
    rec("tags-up-generate-hangs-falls-back", out == "ok" and 1900 < ms < 4000,
        "answer from control after 2s timeout", "%r / %dms" % (out, int(ms)), ms,
        "降级后重试一次；拿不到就返回空串，绝不编造")
    brain.shutdown(); brain.server_close(); ctl.shutdown(); ctl.server_close()

    # 3) 大脑端口根本没开 → 立刻切到主控
    dport = _dead_port()
    ctl, cport = _stub("ok")
    lm, _ = _patched_lm([
        {"id": "brain", "order": 1, "url": "http://127.0.0.1:%d" % dport},
        {"id": "control", "order": 2, "url": "http://127.0.0.1:%d" % cport},
    ])
    t = time.time()
    got = lm.endpoint()
    ms = (time.time() - t) * 1000
    rec("brain-dead-skipped", got.endswith(str(cport)) and ms < 2500,
        "control within 2500ms", "%s / %dms" % (got.split(":")[-1], int(ms)), ms)
    ctl.shutdown(); ctl.server_close()

    # 4) 健康缓存：选中大脑后大脑立刻死掉，30s 内仍复用缓存（不每次重探）
    brain, bport = _stub("ok")
    ctl, cport = _stub("ok")
    lm, _ = _patched_lm([
        {"id": "brain", "order": 1, "url": "http://127.0.0.1:%d" % bport},
        {"id": "control", "order": 2, "url": "http://127.0.0.1:%d" % cport},
    ])
    first = lm.endpoint()
    brain.shutdown(); brain.server_close()
    second = lm.endpoint()
    rec("health-cache-hit-30s", first == second and second.endswith(str(bport)),
        "same url within TTL", second.split(":")[-1], 0, "缓存窗口内不重探，避免每调用一次探活")
    lm._HEALTH["ts"] -= lm.HEALTH_TTL_S + 1
    third = lm.endpoint()
    rec("health-cache-expires", third.endswith(str(cport)),
        "control after TTL", third.split(":")[-1], 0)
    ctl.shutdown(); ctl.server_close()

    # 5) 唯一端点挂死 → generate 必须按时返回空串，不能把调用方挂住
    brain, bport = _stub("hang", 8.0)
    lm, _ = _patched_lm([{"id": "brain", "order": 1, "url": "http://127.0.0.1:%d" % bport}])
    lm._HEALTH = {"ts": time.time(), "url": "http://127.0.0.1:%d" % bport}
    t = time.time()
    out = lm.generate("ping", cls="probe", timeout=2, why="brain-stress")
    ms = (time.time() - t) * 1000
    rec("generate-timeout-returns-empty", out == "" and ms < 5000,
        "empty within 5000ms", "%r / %dms" % (out, int(ms)), ms)
    brain.shutdown(); brain.server_close()

    budget.take()
    return rows


# ---------------------------------------------------------------- 二、真模型小档并发

def _post(url, path, payload, timeout):
    req = urllib.request.Request(url + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _one_call(url, model, timeout):
    t0 = time.time()
    try:
        d = _post(url, "/api/generate", {
            "model": model, "prompt": "用一句话说清「摘要」和「分类」的区别。",
            "stream": False, "think": False, "keep_alive": "5m",
            "options": {"num_predict": 32, "temperature": 0},
        }, timeout)
    except Exception as e:
        return {"ok": False, "err": str(e)[:120], "sec": time.time() - t0, "tok": 0}
    ev = d.get("eval_count") or 0
    dur = (d.get("eval_duration") or 0) / 1e9
    return {"ok": bool(d.get("response")), "sec": time.time() - t0, "tok": ev,
            "tok_s": round(ev / dur, 1) if dur > 0 and ev else 0.0}


def local_load(url, model, levels, per_level, budget):
    try:
        with urllib.request.urlopen(url + "/api/tags", timeout=3) as r:
            tags = json.loads(r.read())
    except Exception as e:
        return {"url": url, "reachable": False, "err": str(e)[:160], "levels": []}
    names = [m.get("name") for m in tags.get("models") or []]
    if model not in names:
        cand = [n for n in names if "4b" in (n or "")] or names
        if not cand:
            return {"url": url, "reachable": True, "err": "no model", "levels": []}
        model = cand[0]

    if not budget.check():
        return {"url": url, "reachable": True, "model": model,
                "levels": [], "err": budget.stop_reason}
    budget.take()
    warm = _one_call(url, model, CALL_TIMEOUT)   # 预热：装载耗时不计入吞吐

    out = []
    for lv in levels:
        if not budget.check():
            break
        t0 = time.time()
        rows = []
        with ThreadPoolExecutor(max_workers=lv) as ex:
            futs = [ex.submit(_one_call, url, model, CALL_TIMEOUT) for _ in range(per_level)]
            for f in futs:
                rows.append(f.result())
                budget.take()
        wall = time.time() - t0
        ok = [r for r in rows if r["ok"]]
        toks = sum(r["tok"] for r in ok)
        out.append({
            "concurrency": lv,
            "calls": len(rows),
            "ok": len(ok),
            "wall_s": round(wall, 2),
            "p50_s": round(statistics.median([r["sec"] for r in ok]), 2) if ok else None,
            "single_tok_s_median": round(statistics.median([r["tok_s"] for r in ok]), 1) if ok else None,
            "aggregate_tok_s": round(toks / wall, 1) if wall > 0 and toks else 0.0,
        })
    return {"url": url, "reachable": True, "model": model,
            "warmup_ok": bool(warm.get("ok")), "levels": out, "raw_calls": budget.calls}


# ---------------------------------------------------------------- 三、容量反推

def plan(local_rows=None):
    """三块纯算术：大脑各座位预期 / 常驻摆放能不能放下 / 漫剧单集需求。
    全是预测，公式与效率区间写在这里；大脑入网当天用 --mode local --url 换实测。"""
    try:
        with open(os.path.join(FLEET, "AGENT-CAPACITY-v1.json"), encoding="utf-8") as f:
            cap = json.load(f)
    except Exception:
        cap = {}

    # 锚点只用来定"理论值→实测"的换算区间；CUDA 侧不直接套 MLX 效率
    base_tok_s = 39.0
    for lv in (local_rows or []):
        if lv.get("single_tok_s_median"):
            base_tok_s = lv["single_tok_s_median"]
    anchor_theo = 200.0 / 3.97          # M1 Pro 200GB/s ÷ 4B nvfp4 3.97GB
    eff_mlx = round(base_tok_s / anchor_theo, 2)
    EFF_1 = (0.28, 0.42)                # 单卡 V100：Volta、无 bf16、KV 与调度开销
    EFF_N = (0.20, 0.32)                # 跨卡切层：PCIe 无 NVLink，再打折

    # (座位, 权重GB, 卡数, 量化, 用途, KV+余量GB)
    seats = [
        ("triage-8B", 8.5, 1, "Q8", "分类/抽取/短判定", 2.5),
        ("review-14B", 28.0, 2, "FP16", "判据复核", 5.0),
        ("creative-32B", 20.0, 2, "Q4", "剧本/台词/长文", 4.0),
        ("embed-0.6B", 1.4, 1, "FP16", "向量与去重", 1.0),
    ]
    bw = 900.0                          # V100 HBM2 GB/s
    est = []
    for name, gb, cards, quant, why, kv in seats:
        theo = cards * bw / gb          # 分卡并行读权重：每卡读自己的那份
        lo, hi = EFF_N if cards > 1 else EFF_1
        est.append({
            "seat": name, "quant": quant, "weight_gb": gb, "cards": cards, "why": why,
            "fits_one_card": gb + kv <= 16.0,
            "vram_gb": round(gb + kv, 1),
            "tok_s_band": [int(theo * lo), int(theo * hi)],
        })

    # 常驻摆放（3×V100=48G）：creative 占 1-2 卡，triage+embed 占第 3 卡
    resident = [e for e in est if e["seat"] in ("creative-32B", "triage-8B", "embed-0.6B")]
    resident_gb = round(sum(e["vram_gb"] for e in resident), 1)
    placement = {
        "resident_set": [e["seat"] for e in resident],
        "resident_gb": resident_gb,
        "usable_gb": 48,
        "on_demand": ["review-14B（复核高峰临时卸 creative，或放 P104 跑小档）"],
        "verdict": ("常驻放得下，余 %.1fG 给 KV 与临时装卸" % (48 - resident_gb))
        if resident_gb <= 48 else "常驻放不下，必须减席或改量化",
        "p104_note": "3×P104 8G 只放向量/小模型，不承接主力（Pascal，无张量核）",
    }

    # 漫剧单集模型需求（对齐 drama-dept-v1 十步 SOP：30 镜、每镜 ≤3 抽）
    shots = 30
    calls = 2 + 1 + shots + 2 + 1
    out_tok = 2500 + 1800 + shots * 70 + 1200 + 800
    decode_tok_s = 18.0                 # 取 32B Q4 预测区间下沿，与 AGENT-CAPACITY 的 18 一致
    decode_min = round(out_tok / decode_tok_s / 60, 1)
    review_min = round(decode_min * 0.3, 1)      # 评审复核按 30% 加
    ep = {"shots": shots, "llm_calls": calls, "out_tokens": out_tok,
          "in_tokens": out_tok * 3,
          "decode_minutes": decode_min, "with_review_minutes": round(decode_min + review_min, 1),
          "assumed_tok_s": decode_tok_s}

    brain = (cap.get("machines") or {}).get("brain") or {}
    budget_min = (brain.get("budget") or {}).get("model_minutes_per_day")
    budget_calls = (brain.get("budget") or {}).get("calls_per_day")
    daily = {
        "brain_budget_minutes": budget_min,
        "brain_budget_calls": budget_calls,
        "assumed_tok_s_in_capacity_file": brain.get("tok_s"),
        "tok_s_vs_prediction": ("预算 18 tok/s 落在预测区间下沿，说明现有额度不虚高"
                               if brain.get("tok_s") and
                               est[2]["tok_s_band"][0] <= brain["tok_s"] <= est[2]["tok_s_band"][1]
                               else "预算取值与预测区间不一致，入网后需重算"),
        "episodes_by_minutes": int(budget_min // max(ep["with_review_minutes"], 0.1)) if budget_min else None,
        "episodes_by_calls": int(budget_calls // calls) if budget_calls else None,
    }
    llm_share = None
    if budget_min:
        llm_share = round(ep["with_review_minutes"] / budget_min * 100, 1)

    return {
        "anchor": {"measured_tok_s": base_tok_s, "mlx_efficiency": eff_mlx,
                   "formula": "预测 tok/s = 卡数×900GB/s ÷ 权重GB × CUDA 效率(单卡 0.28-0.42 / 跨卡 0.20-0.32)",
                   "caveat": "预测，非实测；入网当天 --mode local --url http://<brain>:11434 复跑替换"},
        "brain_seats": est,
        "placement": placement,
        "drama_episode": ep,
        "fleet_capacity": daily,
        "verdict": ("LLM 侧不是漫剧瓶颈：一集含评审约 %.1f 分钟解码，只占大脑日额度的 %s%%；"
                    "真瓶颈在 i2v 抽卡与渲染，V100 跑扩散需单独实测。"
                    % (ep["with_review_minutes"], llm_share))
                   if budget_min else "缺少大脑额度配置，无法反推",
    }


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "ladder", "local", "plan"])
    ap.add_argument("--url", default=DEFAULT_LOCAL, help="local 档的目标端点（入网当天填大脑）")
    ap.add_argument("--levels", default="1,2,4")
    ap.add_argument("--per-level", type=int, default=PER_LEVEL)
    ap.add_argument("--max-calls", type=int, default=MAX_CALLS)
    ap.add_argument("--max-seconds", type=int, default=MAX_SECONDS)
    ap.add_argument("--call-timeout", type=int, default=CALL_TIMEOUT)
    ap.add_argument("--max-swap-mb", type=float, default=MAX_SWAP_MB)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    levels = [int(x) for x in a.levels.split(",") if x.strip()]
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": a.mode,
              "brakes": {"max_calls": a.max_calls, "max_seconds": a.max_seconds,
                         "call_timeout": a.call_timeout, "max_swap_mb": a.max_swap_mb}}
    rc = 0

    if a.mode in ("all", "ladder"):
        print("== 一、端点阶梯（假端点，零模型成本）")
        rows = ladder(a.verbose)
        report["ladder"] = rows
        bad = [r for r in rows if not r["ok"]]
        print("   %d/%d 过" % (len(rows) - len(bad), len(rows)))
        for r in bad:
            print("   FAIL %s: expect=%s got=%s" % (r["case"], r["expect"], r["got"]))
        rc = rc or (1 if bad else 0)

    if a.mode in ("all", "local"):
        print("== 二、真模型小档并发（硬上限 %d 次 / %ds / swap+%dMB）"
              % (a.max_calls, a.max_seconds, a.max_swap_mb))
        budget = Budget(a.max_calls, a.max_seconds, a.max_swap_mb, "local")
        policy_model = "qwen3.5:4b"
        try:
            with open(os.path.join(FLEET, "LOCAL-MODEL-POLICY.json"), encoding="utf-8-sig") as f:
                policy_model = ((json.load(f).get("duties") or {}).get("resident") or {}).get("model") or policy_model
        except Exception:
            pass
        res = local_load(a.url, policy_model, levels, a.per_level, budget)
        res["budget"] = budget.summary()
        report["local"] = res
        if not res.get("reachable"):
            print("   端点不可达：%s" % res.get("err"))
            rc = 2
        else:
            for lv in res["levels"]:
                print("   c=%d  %d/%d ok  p50=%.2fs  单请求 %.1f tok/s  聚合 %.1f tok/s"
                      % (lv["concurrency"], lv["ok"], lv["calls"], lv["p50_s"] or 0,
                         lv["single_tok_s_median"] or 0, lv["aggregate_tok_s"]))
            if res.get("budget", {}).get("stopped_by"):
                print("   已被硬闸叫停：%s（这是设计行为，不是失败）" % res["budget"]["stopped_by"])

    if a.mode in ("all", "plan"):
        print("== 三、容量反推（纯算术，标注为预测）")
        p = plan((report.get("local") or {}).get("levels"))
        report["plan"] = p
        print("   锚点：实测 %.1f tok/s，MLX 效率 %.2f（CUDA 侧另打折）"
              % (p["anchor"]["measured_tok_s"], p["anchor"]["mlx_efficiency"]))
        for e in p["brain_seats"]:
            print("   %-14s %-5s %d卡 %5.1fG  预测 %s tok/s%s"
                  % (e["seat"], e["quant"], e["cards"], e["vram_gb"], e["tok_s_band"],
                     "" if e["fits_one_card"] else "（单卡放不下，必须分卡）"))
        pl = p["placement"]
        print("   常驻：%s = %.1fG / 48G → %s"
              % ("+".join(pl["resident_set"]), pl["resident_gb"], pl["verdict"]))
        print("   漫剧一集：%d 镜 / %d 次调用 / %d 输出 token → 解码 %.1f 分钟（含评审 %.1f）"
              % (p["drama_episode"]["shots"], p["drama_episode"]["llm_calls"],
                 p["drama_episode"]["out_tokens"], p["drama_episode"]["decode_minutes"],
                 p["drama_episode"]["with_review_minutes"]))
        print("   额度对照：%s" % p["fleet_capacity"]["tok_s_vs_prediction"])
        print("   " + p["verdict"])

    report["rc"] = rc
    os.makedirs(STATE, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("→ %s" % os.path.relpath(OUT, ROOT))
    return rc


if __name__ == "__main__":
    sys.exit(main())
