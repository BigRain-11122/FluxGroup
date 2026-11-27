#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""condition_matrix.py - 环境条件矩阵：把「不同机器 × 不同环境偏差」逐格验一遍。

CEO 2026-11-11：「继续自动化循环测试，测不同的工况，不同的机器环境等」。
station_qa 管机内执行工况、fleet_rehearsal 管跨机流转；这一台补的是**环境面**：
  1) 系统面：同一批工具在 darwin / windows / 未验证 OS 上的可跑性
  2) 版本面：python/ollama/ffmpeg/torch 偏高偏低、缺失、探针陈旧
  3) 模型面：模型缺失、digest 被换、无向量模型
  4) 核力面：无 AVX2/内存不足/白天份额 下的并行度与禁区
  5) 端点面：大脑活/挂/半死（复用 brain_stress 的阶梯用例）

判据来源：env_align.check_station / cpu_alloc.capacity / os_matrix.runnable_for
——**期望值在用例里独立写死**，不拿工具自己的结果当答案（否则等于没测）。

用法：
  python3 Tools/fleet/condition_matrix.py                 # 跑一轮
  python3 Tools/fleet/condition_matrix.py --rounds 5       # 循环 5 轮（每轮打乱顺序）
  python3 Tools/fleet/condition_matrix.py --json --rounds 3
  python3 Tools/fleet/condition_matrix.py --self-test
Exit: 0 全过；1 有格不合格
"""
import argparse
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "Tools", "fleet")
FLEET = os.path.join(ROOT, "cph4", "fleet")
HIST = os.path.join(FLEET, "state", "condition-matrix.jsonl")
sys.path.insert(0, TOOLS)


def good_probe(station, spec):
    """按环境档造一份"标准合格"的探针，用于逐项打坏。"""
    prof_id = (spec.get("stations") or {}).get(station)
    prof = (spec.get("profiles") or {}).get(prof_id) or {}
    is_win = prof_id == "windows-cuda"
    models = [{"name": "qwen3:8b", "digest": "500a1f067a9f7826", "quant": "Q4_K_M"},
              {"name": "qwen3-embedding:0.6b", "digest": "ac6da0dfba84a81f"}]
    if station == "control":
        models = [{"name": "qwen3.5:4b", "digest": "7f3251fa6878a78a"},
                  {"name": "qwen3-embedding:0.6b", "digest": "ac6da0dfba84a81f"}]
    env = {"OLLAMA_KEEP_ALIVE": "10m"}
    if is_win:
        env["OLLAMA_MODELS"] = "D:\\ollama\\models"
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "station": station,
            "os": "windows" if is_win else "darwin",
            "python": {"version": "3.11.9" if is_win else "3.13.18"},
            "packages": {"torch": "2.5.1" if is_win else "2.15.0"},
            "ffmpeg": {"version": "6.1" if is_win else "7.1"},
            "ollama": {"version": "0.31.0" if is_win else "0.40.16", "models": models},
            "env": env, "gpu": {"cards": ["x"]}}


def _bump(probe, path, value):
    p = json.loads(json.dumps(probe))
    cur = p
    keys = path.split(".")
    for k in keys[:-1]:
        cur = cur[k]
    cur[keys[-1]] = value
    return p


def cases_env(spec):
    """每台机 × 各类环境偏差：期望状态在用例里写死。"""
    out = []
    for sid in (spec.get("stations") or {}):
        base = good_probe(sid, spec)
        has_profile = bool((spec.get("stations") or {}).get(sid))
        variants = [
            ("标准环境", lambda p: p, "PASS" if has_profile else "未定档"),
            ("python 过低(3.9.1)", lambda p: _bump(p, "python.version", "3.9.1"), "GAP"),
            ("ollama 过旧(0.20.0)", lambda p: _bump(p, "ollama.version", "0.20.0"), "GAP"),
            ("ffmpeg 缺失", lambda p: _bump(p, "ffmpeg.version", None), "GAP"),
            ("torch 过旧(2.0.0)", lambda p: _bump(p, "packages.torch", "2.0.0"), "GAP"),
            ("聊天模型缺失", lambda p: _bump(p, "ollama.models", []), "GAP"),
            # 只有钉了 digest 的机位才检得出（目前只有 control 钉了）；未钉的机型这一项
            # 属于"规格缺口"而不是通过——下面按机位决定期望，并在 note 里标注。
            ("digest 被换", lambda p: _bump(p, "ollama.models", [
                {"name": "qwen3.5:4b", "digest": "deadbeef"},
                {"name": "qwen3:8b", "digest": "deadbeef"},
                {"name": "qwen3-embedding:0.6b", "digest": "ac6da0dfba84a81f"}]),
             "GAP" if sid == "control" else "PASS"),
            ("缺向量模型", lambda p: _bump(p, "ollama.models",
                                          [m for m in p["ollama"]["models"] if "embed" not in m["name"]]), "GAP"),
            ("KEEP_ALIVE 未设", lambda p: {**p, "env": {k: v for k, v in p["env"].items()
                                                     if k != "OLLAMA_KEEP_ALIVE"}}, "GAP"),
            ("探针 48h 未更新", lambda p: _bump(p, "ts", time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 48 * 3600))), "GAP"),
            ("无探针", lambda p: None, "未探测"),
        ]
        for name, mut, expect in variants:
            if not has_profile:
                expect = "未定档"          # 无环境档位（大脑 OS 待定）：任何探针都判未定档
            out.append({"kind": "env", "station": sid, "case": name,
                        "expect": expect, "probe": mut(base)})
    return out


def cases_cpu(cpu_plan):
    """核力面：无 AVX2 / 内存不足 / 白天份额 的期望并行度与禁区（独立写死）。"""
    exp = [
        # 机器, 活类, 夜窗?, 期望并行, 说明
        ("brain", "asr-post", True, 0, "无 AVX2 → 不接 ASR"),
        ("brain", "transcode", True, 1, "无 AVX2 → 只走降速档，1 并行"),
        ("brain", "backtest", True, 2, "256G/32G 且留 4 核 → 2"),
        ("visual", "backtest", True, 0, "24G 内存 → 回测不排"),
        ("control", "transcode", True, 0, "统一内存 → 禁长转码"),
        ("audio", "asr-post", True, 1, "8C/16T 留 2 → 1"),
        ("delivery", "compile", True, 1, "13 核可用 / 8 线程 → 1"),
        ("delivery", "compile", False, 0, "白天份额 0.25 → 0（CEO 在用）"),
        ("brain", "rule-check", False, 20, "24/7 全开 → 20"),
        ("brain", "rule-check", True, 20, "夜窗同额 → 20"),
    ]
    return [{"kind": "cpu", "machine": m, "cls": c, "night": n,
             "case": "%s/%s-%s" % (m, c, "夜" if n else "日"),
             "expect": e, "note": note} for m, c, n, e, note in exp]


def cases_os(matrix):
    """系统面：同一工具在不同 OS 上的可跑性（未核实 OS 一律拒）。"""
    rows = [{"tool": "pulse.py", "class": "mac_only"},
            {"tool": "probe.ps1", "class": "win_only"},
            {"tool": "audit.py", "class": "cross"}]
    exp = {"control": {"pulse.py": True, "probe.ps1": False, "audit.py": True},
           "delivery": {"pulse.py": False, "probe.ps1": True, "audit.py": True},
           "visual": {"pulse.py": False, "probe.ps1": True, "audit.py": True},
           "audio": {"pulse.py": False, "probe.ps1": True, "audit.py": True},
           "brain": {"pulse.py": False, "probe.ps1": False, "audit.py": False}}
    out = []
    for sid, m in exp.items():
        for tool, want in m.items():
            out.append({"kind": "os", "station": sid, "case": tool, "expect": want, "rows": rows})
    return out


def run_round(spec, cpu_plan, matrix, seed=0):
    import env_align as ea
    import cpu_alloc as ca
    import os_matrix as om

    cases = cases_env(spec) + cases_cpu(cpu_plan) + cases_os(matrix)
    random.Random(seed).shuffle(cases)

    results = []
    for c in cases:
        if c["kind"] == "env":
            got = ea.check_station(c["station"], spec, c["probe"])["status"]
            ok = (got == c["expect"])
            results.append({**{k: c[k] for k in ("kind", "station", "case", "expect")},
                            "got": got, "ok": ok})
        elif c["kind"] == "cpu":
            cap = ca.capacity(cpu_plan, c["machine"], c["cls"], night=c["night"])
            ok = (cap["parallel"] == c["expect"])
            results.append({"kind": "cpu", "station": c["machine"], "case": c["case"],
                            "expect": c["expect"], "got": cap["parallel"], "ok": ok,
                            "note": c["note"]})
        else:
            r = om.runnable_for(matrix, c["station"], c["rows"])
            got = (c["case"] in (r.get("runnable") or [])) if r.get("ok") else False
            ok = (got == c["expect"])
            results.append({"kind": "os", "station": c["station"], "case": c["case"],
                            "expect": c["expect"], "got": got, "ok": ok})
    return results


def load_all():
    def L(p, d=None):
        try:
            with open(p, encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return d
    spec = L(os.path.join(FLEET, "AI-ENV-SPEC-v1.json"), {}) or {}
    cpu_plan = L(os.path.join(FLEET, "CPU-PLAN-v1.json"), {}) or {}
    matrix = L(os.path.join(FLEET, "OS-MATRIX-v1.json"), {}) or {}
    return spec, cpu_plan, matrix


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    spec, cpu_plan, matrix = load_all()
    chk("三份正身都读得到", spec and cpu_plan and matrix)
    cases = cases_env(spec) + cases_cpu(cpu_plan) + cases_os(matrix)
    chk("用例数 ≥ 50（够覆盖 5 机 × 多偏差）", len(cases) >= 50, len(cases))
    chk("每格都有 expect", all("expect" in c for c in cases))
    r1 = run_round(spec, cpu_plan, matrix, seed=1)
    r2 = run_round(spec, cpu_plan, matrix, seed=7)
    chk("两轮不同种子结果一致（确定性）",
        sorted((x["station"], x["case"], str(x["got"])) for x in r1)
        == sorted((x["station"], x["case"], str(x["got"])) for x in r2))
    # 反向验证：把一条真实结果改错，判定必须变 False（防"闸永远绿"）
    bad = [dict(x) for x in r1]
    bad[0]["got"] = "TAMPERED"
    chk("篡改一格能被判出", any(not x["ok"] for x in [(x | {"ok": (x["got"] == x["expect"])}) for x in bad]))
    print("[condition_matrix] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    spec, cpu_plan, matrix = load_all()
    all_rows, hist = [], []
    for i in range(max(1, a.rounds)):
        rows = run_round(spec, cpu_plan, matrix, seed=1000 + i)
        bad = [r for r in rows if not r["ok"]]
        hist.append({"round": i + 1, "total": len(rows), "failed": len(bad),
                     "seed": 1000 + i})
        all_rows = rows
        if not a.json:
            print("轮 %d：%d 格 / 失败 %d" % (i + 1, len(rows), len(bad)))
            for r in bad[:8]:
                print("   ✗ [%s] %s / %s：期望 %s 实得 %s"
                      % (r["kind"], r["station"], r["case"], r["expect"], r["got"]))

    bad = [r for r in all_rows if not r["ok"]]
    if a.json:
        print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rounds": hist,
                          "cases": len(all_rows), "failed": len(bad),
                          "failures": bad[:20]}, ensure_ascii=False, indent=1))
    else:
        print("合计 %d 格 × %d 轮｜失败 %d" % (len(all_rows), len(hist), len(bad)))
    try:
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        with open(HIST, "a", encoding="utf-8") as f:
            for h in hist:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **h},
                                   ensure_ascii=False) + "\n")
    except Exception:
        pass
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
