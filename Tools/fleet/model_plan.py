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
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
MATRIX_V2 = os.path.join(FLEET, "MODEL-MONITOR-MATRIX-v2.json")
MATRIX = MATRIX_V2 if os.path.exists(MATRIX_V2) else os.path.join(FLEET, "MODEL-MONITOR-MATRIX-v1.json")
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
                  "ctx": m.get("context_length"),
                  "expires": str(m.get("expires_at") or "")[:19]} for m in ms]
    except Exception as e:
        return {"_error": str(e)[:80]}


def seat_of_model(name, duties):
    """ps 里的模型名 → 策略座位名（精确优先，再做一次去 -mlx 的宽松匹配）。"""
    name = str(name or "")
    for seat, d in (duties or {}).items():
        if isinstance(d, dict) and (d.get("model") or "") == name:
            return seat
    base = name.replace("-mlx", "")
    for seat, d in (duties or {}).items():
        if isinstance(d, dict) and (d.get("model") or "").replace("-mlx", "") == base:
            return seat
    return None


def tier_errors(tiers, want_res, slots):
    """分档规格判据（纯函数，便于负控）：常驻档要齐、槽位要够、keep_alive 要对。

    Why 单独抽出来：2026-11-14 实测发现本函数的前身在 main 里直接调 subprocess/re，
    却没有 import 这两个模块，异常被 `except Exception: pass` 吞掉 —— E-SLOTS 这项
    「加载槽位够不够」的检查从上线起**一次都没跑过**，看着绿其实是空的。
    抽成纯函数后可以拿篡改过的档位表反向验证它真的会报警。
    """
    errs = []
    tiers = tiers or {}
    for need in want_res:
        if need not in tiers:
            errs.append("E-TIER: 缺常驻档 %s（只剩单一大模型=CEO 明确反对）" % need)
    # 加载槽位必须 ≥ 常驻档数，否则新档进来会挤掉旧档（实测 3 槽挤掉 8B）。
    # 未显式设置时按 Ollama 默认 3（1 GPU × 3）算，不许因为读不到就跳过判据。
    if slots is None:
        slots = 3
    if int(slots) < len(want_res):
        errs.append("E-SLOTS: OLLAMA_MAX_LOADED_MODELS=%s 小于常驻档数 %d（会互相驱逐）"
                    % (slots, len(want_res)))
    for k, t in tiers.items():
        if not isinstance(t, dict):
            continue
        ka = str(t.get("keep_alive"))
        is_mlx = (str(t.get("runner") or "").lower() == "mlx"
                  or "mlx" in str(t.get("model") or "").lower())
        if is_mlx:
            # MLX runner 对 keep_alive=0 会卡在 Stopping 且再也加载不上（2026-11-11 实测）：
            # 这是与"非常驻必须写 0"相反的一条，必须单独判，否则等于把模型弄坏。
            if ka in ("0", "0.0", "0s"):
                errs.append("E-KEEPALIVE-MLX: %s 是 MLX 档却 keep_alive=0（会卡在 Stopping 再也加载不上）" % k)
        elif t.get("resident") is False and ka not in ("0", "0s"):
            errs.append("E-KEEPALIVE: %s 非常驻却 keep_alive=%s（会悄悄占住常驻）" % (k, ka))
    return errs


def slots_env():
    """读 ollama serve 的 OLLAMA_MAX_LOADED_MODELS；读不到返回 None（按默认 3 算）。"""
    try:
        pg = subprocess.run(["pgrep", "-f", "ollama serve"],
                            capture_output=True, text=True, timeout=10).stdout.split()
        if not pg:
            return None
        env_txt = subprocess.run(["ps", "-E", "-p", pg[0]],
                                 capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"OLLAMA_MAX_LOADED_MODELS=(\d+)", env_txt)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def selftest():
    """负控：改坏一格必须被抓到；正确配置必须零告警。"""
    good = {
        "resident": {"model": "qwen3.5:4b-mlx", "keep_alive": "10m", "resident": True},
        "big": {"model": "qwen3.5:9b-mlx", "keep_alive": "10m", "resident": True, "runner": "mlx"},
        "embedding": {"model": "qwen3-embedding:0.6b", "keep_alive": "10m", "resident": True},
        "triage": {"model": "qwen3.5:2b", "keep_alive": "1m", "resident": False, "runner": "mlx"},
    }
    want = ["resident", "big", "embedding"]
    cases = [
        ("正确三档", good, want, 3, []),
        ("槽位不足", good, want, 2, ["E-SLOTS"]),
        ("槽位未设置按默认 3", good, want, None, []),
        ("常驻档缺一", {k: v for k, v in good.items() if k != "big"}, want, 3, ["E-TIER"]),
        ("MLX 写 0", dict(good, big={"model": "qwen3.5:9b-mlx", "keep_alive": "0",
                                    "resident": True, "runner": "mlx"}), want, 3,
         ["E-KEEPALIVE-MLX"]),
        ("非 MLX 按需写 1m", dict(good, polish={"model": "some:7b", "keep_alive": "1m",
                                               "resident": False}), want, 3, ["E-KEEPALIVE"]),
    ]
    bad = 0
    for name, tiers, wr, slots, want_codes in cases:
        got = tier_errors(tiers, wr, slots)
        hit = [c for c in want_codes if not any(e.startswith(c) for e in got)]
        extra = [e for e in got if not any(e.startswith(c) for c in want_codes)]
        ok = (not hit) and (not extra)
        bad += 0 if ok else 1
        print("[selftest] %-18s %s %s" % (name, "PASS" if ok else "FAIL",
                                          "" if ok else "缺=%s 多=%s" % (hit, extra)))
    print("[selftest] %s" % ("PASS" if not bad else "FAIL %d" % bad))
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    mx = jload(MATRIX)
    lp = jload(LOCAL)
    if not mx or not lp:
        print(json.dumps({"verdict": "E-CONFIG", "detail": "矩阵或策略缺失"}, ensure_ascii=False))
        return 2

    duties = lp.get("duties") or {}
    # 白名单取自"策略文件里所有座位声明的模型"，不再手写座位名——
    # 手写名单会漏（加了 triage/on_demand 后本项立刻误报 E-NAME）。
    known = {((v or {}).get("model") or "").strip()
             for v in duties.values() if isinstance(v, dict)}
    known.discard("")
    seats = mx.get("tiers") or mx.get("seats") or {}
    budget = mx.get("budget") or {}
    warns, errs = [], []

    # 1) 矩阵不得另立模型名
    for sid, s in seats.items():
        m = str((s or {}).get("model") or "").strip()
        if m and m not in known:
            errs.append("E-NAME: 座位 %s 的模型 %s 不在 LOCAL-MODEL-POLICY（单一源）" % (sid, m))

    # 1b) 分档规格（v2）：三档常驻必须齐；按需档必须用完即卸；加载槽位要够
    if mx.get("tiers"):
        want_res = (budget.get("resident_set") or ["big", "resident", "embedding"])
        errs += tier_errors(mx.get("tiers") or {}, want_res, slots_env())

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
        cap = float(budget.get("resident_gb_limit")
                    or budget.get("resident_cap_gb") or 11.0)
        hard = float(budget.get("peak_gb_limit")
                     or budget.get("peak_cap_gb") or 16.0)
        if peak > hard:
            errs.append("E-MEM: 驻留 %.1fGB 超峰值上限 %.1fGB" % (peak, hard))
        elif peak > cap:
            warns.append("W-MEM: 驻留 %.1fGB 超常驻上限 %.1fGB" % (peak, cap))
        for x in live:
            if x["name"] not in known:
                warns.append("W-STRAY: %s 不在白名单，应让位" % x["name"])
        # 上下文必须与策略一致：已加载的 runner 不会因为新请求要更大 ctx 就重载
        # （2026-11-14 实测：策略写 32768、请求也发 32768，ps 仍报 8192，只有 ollama stop
        #   后重载才生效）。不等就意味着长证据被静默截断，而闸看不出来——必须报出来。
        for x in live:
            seat = seat_of_model(x["name"], duties)
            want_ctx = int(((duties.get(seat) or {}) if seat else {}).get("num_ctx") or 0)
            got_ctx = int(x.get("ctx") or 0)
            if want_ctx and got_ctx and got_ctx < want_ctx:
                warns.append("W-CTX: %s 装载 ctx=%d < 策略 %d（已装 runner 不会重载，长输入会被静默截断；"
                             "执行 ollama stop %s 后再预热一次）"
                             % (x["name"], got_ctx, want_ctx, x["name"]))

    verdict = "FAIL" if errs else ("WARN" if warns else "PASS")
    L = ["# 模型排班 %s" % __import__("time").strftime("%Y-%m-%dT%H:%M:%S"), ""]
    L.append("判据：**%s**｜常驻上限 %sGB / 峰值 %sGB / 办公预留 %sGB"
             % (verdict, budget.get("resident_gb_limit") or budget.get("resident_cap_gb"),
                budget.get("peak_gb_limit") or budget.get("peak_cap_gb"),
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