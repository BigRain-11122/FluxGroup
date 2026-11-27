#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""env_align.py - 主控侧：把各机自采的 AI 环境与标准对齐，逐台判 PASS/GAP/STALE/未探测。

标准=cph4/fleet/AI-ENV-SPEC-v1.json；事实=cph4/fleet/env/<station>.json（由 env_probe.py 产出）。
「随时更新」的判据就落在这里：探针超过 max_age_hours 即判 STALE，STALE 不算通过。

用法：
  python3 Tools/fleet/env_align.py            # 打印对齐表（有 GAP/STALE rc=1）
  python3 Tools/fleet/env_align.py --json     # 机器可读
  python3 Tools/fleet/env_align.py --self-test
"""
import argparse
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SPEC = os.path.join(FLEET, "AI-ENV-SPEC-v1.json")
ENVDIR = os.path.join(FLEET, "env")


def _load(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def ver(text):
    """把 '3.13.18' / '7.1' / 'ffmpeg 7.1' 解析成 (3,13,18)。取不到返回 None。"""
    if text is None:
        return None
    nums = re.findall(r"\d+", str(text))
    return tuple(int(n) for n in nums[:3]) if nums else None


def _cmp(a, b):
    n = max(len(a), len(b))
    a = tuple(list(a) + [0] * (n - len(a)))
    b = tuple(list(b) + [0] * (n - len(b)))
    return (a > b) - (a < b)


def satisfies(have, spec, tag=""):
    """支持 '>=3.11,<3.14'、'>=2' 这类区间；纯等值直接比。"""
    h = ver(have)
    if h is None:
        return False, "取不到版本号"
    for part in str(spec).split(","):
        part = part.strip()
        m = re.match(r"(>=|<=|>|<|==)?\s*(.+)", part)
        op = m.group(1) or "=="
        target = ver(m.group(2))
        if target is None:
            if part in str(have):        # 非版本型约束（如盘符模板）
                continue
            return False, "约束不可解析：%s" % part
        c = _cmp(h, target)
        ok = {">=": c >= 0, ">": c > 0, "<=": c <= 0, "<": c < 0, "==": c == 0}[op]
        if not ok:
            return False, "%s 不满足 %s" % (have, part)
    return True, "ok"


def _age_h(ts):
    try:
        return (time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))) / 3600.0
    except Exception:
        return None


def check_station(sid, spec, probe, now_h=None):
    """单台对齐：返回 {"status", "gaps": [...], "notes": [...]}。"""
    gaps, notes = [], []
    profile_id = (spec.get("stations") or {}).get(sid)
    if not profile_id:
        return {"station": sid, "status": "未定档",
                "gaps": ["该机没有对应环境档位（OS 待定或未入网）：先定系统再定环境"],
                "notes": notes}
    prof = (spec.get("profiles") or {}).get(profile_id) or {}
    if not probe:
        return {"station": sid, "status": "未探测", "gaps": ["没有 env/%s.json：该机还没跑过探针" % sid],
                "notes": notes}

    age = _age_h(probe.get("ts"))
    max_age = float((spec.get("policy") or {}).get("max_age_hours") or 24)
    if age is None:
        gaps.append("探针文件没有可解析时间戳")
    elif age > max_age:
        gaps.append("探针已 %.1fh 未更新（阈值 %gh）" % (age, max_age))

    # 版本面
    pairs = [("python", probe.get("python", {}).get("version")),
             ("ollama", probe.get("ollama", {}).get("version")),
             ("ffmpeg", probe.get("ffmpeg", {}).get("version"))]
    if prof.get("torch"):
        pairs.append(("torch", (probe.get("packages") or {}).get("torch")))
    for name, have in pairs:
        want = prof.get(name)
        if not want:
            continue
        if not have:
            gaps.append("%s 未装或未采到（要求 %s）" % (name, want))
            continue
        ok, why = satisfies(have, want, name)
        if not ok:
            gaps.append("%s %s" % (name, why))

    # 环境变量
    have_env = probe.get("env") or {}
    for k, want in (prof.get("env") or {}).items():
        if want.startswith("<"):          # 模板值：只要求存在
            if k not in have_env:
                gaps.append("环境变量 %s 未设置（模板 %s）" % (k, want))
            continue
        hv = have_env.get(k)
        if hv is None:
            gaps.append("环境变量 %s 未设置（要求 %s）" % (k, want))
            continue
        if want.startswith(">="):
            a, b = ver(hv), ver(want)
            if a and b and _cmp(a, b) < 0:
                gaps.append("环境变量 %s=%s 低于要求 %s" % (k, hv, want))
        elif str(hv) != str(want):
            gaps.append("环境变量 %s=%s 与标准 %s 不一致" % (k, hv, want))
    # 软项：默认值已能满足时不算缺口，只记提醒（2026-11-11：Ollama 默认 MAX_LOADED=3×GPU 已够两席共存）
    for k, want in (prof.get("soft_env") or {}).items():
        hv = have_env.get(k)
        if hv is None:
            notes.append("软项 %s 未显式设置（按默认值运行，要求 %s）" % (k, want))
        elif str(want).startswith(">="):
            a, b = ver(hv), ver(want)
            if a and b and _cmp(a, b) < 0:
                gaps.append("环境变量 %s=%s 低于要求 %s" % (k, hv, want))

    # 模型面
    models = {m.get("name"): m for m in (probe.get("ollama", {}).get("models") or [])}
    req = (spec.get("station_models") or {}).get(sid) or {}
    for name in req.get("required") or []:
        if name not in models:
            gaps.append("缺模型 %s" % name)
            continue
        pin = (req.get("pinned_digest") or {}).get(name)
        if pin:
            d = (models[name].get("digest") or "")
            if not d.startswith(pin):
                gaps.append("模型 %s digest=%s 与钉住值 %s 不符（权重被换过？）" % (name, d[:8], pin))
    if req.get("any_of"):
        if not any(n in models for n in req["any_of"]):
            gaps.append("聊天模型一个都没有（任一只需其一：%s）" % "、".join(req["any_of"]))
    if req.get("required_embed") and not any("embedding" in (n or "") for n in models):
        gaps.append("缺向量模型（embedding）")

    if not models:
        notes.append("模型清单为空：Ollama 可能未运行")
    age_txt = "%.1fh" % age if age is not None else "?"
    return {"station": sid, "profile": profile_id, "status": "PASS" if not gaps else "GAP",
            "gaps": gaps, "notes": notes, "probe_age_h": age, "age_txt": age_txt,
            "python": probe.get("python", {}).get("version"),
            "ollama": probe.get("ollama", {}).get("version"),
            "ffmpeg": probe.get("ffmpeg", {}).get("version"),
            "models": sorted(models), "os": probe.get("os")}


def align(spec=None, envdir=ENVDIR):
    spec = spec or _load(SPEC, {}) or {}
    probes = {}
    for p in glob.glob(os.path.join(envdir, "*.json")):
        d = _load(p, {}) or {}
        sid = d.get("station") or os.path.splitext(os.path.basename(p))[0]
        probes[sid] = d
    rows = [check_station(sid, spec, probes.get(sid)) for sid in (spec.get("stations") or {})]
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "spec": os.path.basename(SPEC), "rows": rows}


def section_lines(report):
    """给 FLEET-SPEC 用的一段 markdown。"""
    rows = report.get("rows") or []
    bad = [r for r in rows if r["status"] != "PASS"]
    L = ["| 工位 | 环境档 | 判定 | python | ollama | ffmpeg | 探针年龄 | 缺口 |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["station"], r.get("profile") or "—", r["status"],
            r.get("python") or "—", r.get("ollama") or "—", r.get("ffmpeg") or "—",
            r.get("age_txt") or "—",
            "；".join(r["gaps"][:2]) + ("（等 %d 项）" % len(r["gaps"]) if len(r["gaps"]) > 2 else "")
            if r["gaps"] else "—"))
    L.append("")
    L.append("标准=`cph4/fleet/AI-ENV-SPEC-v1.json`；事实=`cph4/fleet/env/<工位>.json`（由 `env_probe.py` 各机自采）；"
             "超过 24h 未更新判 STALE。%d 台达标 / %d 台待办。" % (len(rows) - len(bad), len(bad)))
    return L


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    spec = _load(SPEC, {}) or {}
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    good = {"ts": now, "station": "control", "os": "darwin",
            "python": {"version": "3.13.18"}, "ffmpeg": {"version": "7.1"},
            "packages": {"torch": "2.15.0"},
            "ollama": {"version": "0.40.16", "models": [
                {"name": "qwen3.5:4b", "digest": "7f3251fa6878a78a"},
                {"name": "qwen3-embedding:0.6b", "digest": "ac6da0dfba84a81f"}]},
            "env": {"OLLAMA_KEEP_ALIVE": "10m", "OLLAMA_MAX_LOADED_MODELS": "3"}}

    r = check_station("control", spec, good)
    chk("配置齐全 -> PASS", r["status"] == "PASS", r)

    bad = json.loads(json.dumps(good))
    bad["python"]["version"] = "3.9.1"
    r = check_station("control", spec, bad)
    chk("python 过低 -> GAP", r["status"] == "GAP" and any("python" in g for g in r["gaps"]), r["gaps"])

    bad2 = json.loads(json.dumps(good))
    bad2["ollama"]["models"][0]["digest"] = "deadbeef"
    r = check_station("control", spec, bad2)
    chk("模型 digest 不符 -> GAP", any("digest" in g for g in r["gaps"]), r["gaps"])

    bad3 = json.loads(json.dumps(good))
    bad3["env"].pop("OLLAMA_KEEP_ALIVE")
    r = check_station("control", spec, bad3)
    chk("缺环境变量 -> GAP", any("OLLAMA_KEEP_ALIVE" in g for g in r["gaps"]), r["gaps"])

    stale = json.loads(json.dumps(good))
    stale["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 48 * 3600))
    r = check_station("control", spec, stale)
    chk("探针超 24h -> GAP(陈旧)", any("未更新" in g for g in r["gaps"]), r["gaps"])

    chk("无探针 -> 未探测", check_station("delivery", spec, None)["status"] == "未探测")
    chk("无档位（大脑 OS 待定）-> 未定档", check_station("brain", spec, good)["status"] == "未定档")

    rep = align(spec)
    chk("真实对齐能跑出 5 台行", len(rep["rows"]) == len(spec.get("stations") or {}), len(rep["rows"]))
    chk("能渲染成 markdown 段", any("| 工位 |" in x for x in section_lines(rep)))

    print("[env_align] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rep = align()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print("%-9s %-14s %-8s %-10s %-9s %-8s %s"
              % ("工位", "环境档", "判定", "python", "ollama", "探针", "缺口"))
        for r in rep["rows"]:
            print("%-9s %-14s %-8s %-10s %-9s %-8s %s"
                  % (r["station"], r.get("profile") or "—", r["status"],
                     r.get("python") or "—", r.get("ollama") or "—", r.get("age_txt") or "—",
                     ("；".join(r["gaps"])[:70]) if r["gaps"] else ""))
    try:
        os.makedirs(os.path.join(FLEET, "state"), exist_ok=True)
        with open(os.path.join(FLEET, "state", "ai-env-align.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 0 if all(r["status"] == "PASS" for r in rep["rows"]) else 1


if __name__ == "__main__":
    sys.exit(main())
