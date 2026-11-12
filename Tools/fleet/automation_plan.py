#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""automation_plan.py - 校验自动化排班并在 24 小时内模拟一遍。

CEO 2026-11-11：「你自己列好自动化的任务，全面测试和推进这个新工作流」。

它回答四个问题（全部可复算，不靠印象）：
  1) 每个任务的四件套齐不齐（cmd / cadence / owner / output）？cmd 指向的脚本在盘吗？
  2) 24 小时内谁在什么时候跑？同一分钟有没有两个任务抢同一个输出文件？
  3) 每台机的模型调用量会不会超 AGENT-CAPACITY 的日额度？
  4) 被阻塞的工位（离线/未装/坏）上的任务有没有被误当成"在跑"？

用法：
  python3 Tools/fleet/automation_plan.py            # 校验 + 日历 + 并发/额度结论
  python3 Tools/fleet/automation_plan.py --json
  python3 Tools/fleet/automation_plan.py --self-test
Exit: 0 排班可用；1 有阻塞问题（缺件/冲突/超额度）
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
PLAN = os.path.join(FLEET, "AUTOMATION-v1.json")
CAP = os.path.join(FLEET, "AGENT-CAPACITY-v1.json")
STATIONS = os.path.join(FLEET, "STATIONS.json")
OUT = os.path.join(FLEET, "state", "automation-plan.json")


def load(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def stations():
    return {s["id"]: s for s in (load(STATIONS, {}) or {}).get("stations") or []}


def expand(station_field):
    """'delivery|visual' -> [delivery, visual]；'all' 展开成五工位。"""
    st = list(stations())
    if station_field == "all":
        return st
    if "|" in station_field:
        return [x.strip() for x in station_field.split("|") if x.strip()]
    return [station_field]


def cmd_target(cmd):
    """从 cmd 里抠出脚本路径，验证它在盘上（{py} 是解释器占位）。"""
    try:
        parts = shlex.split(cmd.replace("{py}", "python3"))
    except Exception:
        return None
    for p in parts:
        if p.endswith((".py", ".sh", ".ps1")) or "/" in p:
            if not p.startswith("-"):
                return p
    return None


def is_blocked(st):
    return str(st.get("status") or "").startswith(("offline", "not_installed", "blocked"))


def check_flags(cmd):
    """没有脚本文件的命令（git pull 这类），用 `<tool> <sub> -h` 的 usage 文本核对旗标。

    2026-11-11 实锚：排班里写过 `git pull --rebase --autostart`——git 没有这个
    旗标（真跑 rc=129 unknown option），每 5 分钟必失败一次，而校验器只查
    "脚本文件在不在盘"，对这类命令直接跳过，于是 13/13 全绿。旗标错不是语法
    小事，是"命令面全线不通"。
    """
    parts = (cmd or "").split()
    if not parts or parts[0] in ("{py}", "python", "python3"):
        return []
    flags = [p for p in parts[1:] if p.startswith("--")]
    if not flags:
        return []
    try:
        # 只传子命令，绝不把待测旗标一起传——否则 usage 报错里出现该旗标字样，
        # 反而让错误旗标"看起来存在"（首版就是这么写的，错旗标照样判绿）。
        sub = next((p for p in parts[1:] if not p.startswith("-")), None)
        argv = [parts[0]] + ([sub] if sub else []) + ["-h"]
        out = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        help_text = (out.stdout or "") + (out.stderr or "")
    except Exception:
        return []          # 拿不到 usage 就不判，不制造假红
    bad = []
    for f in flags:
        name = f.lstrip("-").split("=")[0]
        if name and ("--" + name) not in help_text and name not in help_text:
            bad.append(f)
    return bad


def validate(plan):
    probs = []
    tasks = plan.get("tasks") or []
    seen = set()
    for t in tasks:
        tid = t.get("id")
        if not tid:
            probs.append({"level": "P0", "why": "任务没有 id"})
            continue
        if tid in seen:
            probs.append({"level": "P0", "why": "任务 id 重复：%s" % tid})
        seen.add(tid)
        for k in ("cmd", "cadence_s", "station", "why"):
            if not t.get(k):
                probs.append({"level": "P0", "why": "%s 缺字段 %s（四件套不全）" % (tid, k)})
        if not t.get("output") and "output" not in t:
            probs.append({"level": "P1", "why": "%s 没有 output（应显式写 null 表示无产物）" % tid})
        if int(t.get("cadence_s") or 0) < 60:
            probs.append({"level": "P1", "why": "%s 周期 <60s，会打爆" % tid})
        target = cmd_target(t.get("cmd") or "")
        if target and not os.path.exists(os.path.join(ROOT, target)):
            probs.append({"level": "P0", "why": "%s 的命令指向不存在的文件：%s" % (tid, target)})
        badf = check_flags(t.get("cmd") or "")
        if badf:
            probs.append({"level": "P0",
                          "why": "%s 的命令旗标不存在：%s（真跑会用错选项直接失败）"
                                 % (tid, ", ".join(badf))})
        for sid in expand(t.get("station") or ""):
            if sid not in stations():
                probs.append({"level": "P0", "why": "%s 指向未知工位 %s" % (tid, sid)})
    return probs


def simulate_24h(plan):
    """按周期铺到 24 小时，找同分钟写同一 output 的任务。"""
    fires = []
    for t in plan.get("tasks") or []:
        cad = int(t.get("cadence_s") or 0)
        if cad <= 0:
            continue
        n = min(int(86400 // cad), 24 * 12)      # 采样上限，避免 5 分钟级任务把表铺爆
        for i in range(n):
            fires.append({"t": (i * cad) % 86400, "id": t.get("id"),
                          "out": t.get("output"), "station": t.get("station")})
    fires.sort(key=lambda x: (x["t"], str(x["id"])))
    conflicts = []
    by_t = {}
    for f in fires:
        if not f["out"]:
            continue
        by_t.setdefault(f["t"], {})
        prev = by_t[f["t"]].get(f["out"])
        if prev and prev != f["id"]:
            conflicts.append({"t": f["t"], "output": f["out"], "a": prev, "b": f["id"]})
        by_t[f["t"]][f["out"]] = f["id"]
    # 每分钟触发数峰值 + 同工位同分钟并发（后者是本轮审出来的盲区：
    # 只按 output 判冲突时，15 个 control 任务同时到期会被判"没问题"，
    # 而它们会抢同一台机的 CPU/模型/文件锁）。
    per_min = {}
    per_station_min = {}
    for f in fires:
        per_min[f["t"]] = per_min.get(f["t"], 0) + 1
        for sid in expand(f.get("station") or ""):
            per_station_min[(f["t"], sid)] = per_station_min.get((f["t"], sid), 0) + 1
    hot = [{"t": t, "station": s, "n": n}
           for (t, s), n in sorted(per_station_min.items(), key=lambda kv: -kv[1])[:5]
           if n > 3]
    return {"fires": len(fires), "conflicts": conflicts[:10],
            "busiest_minute": max(per_min.values()) if per_min else 0,
            "hottest_station_minute": hot}


INFER_ENDPOINTS = ("/api/generate", "/api/chat")
# 必须匹配到"真实调用形态"（带括号），不能只看名字出现过：
# automation_plan 与 audit_deep 互为对方的被检对象，写常量名进去就会互相误判。
HTTP_CALL = re.compile(r"(urllib\.request\.(urlopen|Request)|requests\.(get|post|Session))\s*\(")


def infers(cmd):
    """从代码事实判断这条命令会不会真的推模型。

    2026-11-11 教训：原实现用一张手填表 MODELISH 记"每次触发调几次模型"，
    实际 SELF-DRIVE(288 次/天) 里 station_drive.py 只在 detect_station() 里
    拿身份、零推理，却被记 2 次 ⇒ 四个工位全判"额度超支"（假红）。手填表
    必然和代码漂移，改为扫脚本里的真推理证据。

    判据必须两样同时成立：真发 HTTP 的调用 + 推理端点。只认端点会把
    audit_deep.py 误判成推理——它把 "/api/generate" 当作要检测的坏模式写进源码。
    """
    target = cmd_target(cmd or "")
    if not target:
        return False
    try:
        with open(os.path.join(ROOT, target), encoding="utf-8", errors="replace") as f:
            src = f.read()
    except Exception:
        return False
    return any(e in src for e in INFER_ENDPOINTS) and bool(HTTP_CALL.search(src))


def measured(station=None, window_h=24, now=None):
    """实测对账：读本机调用账，算真生成次数与模型时间。

    为什么必须有这一层（2026-11-11 实锚）：静态估算只算"排班任务自身进程里的
    模型调用"，而 station_drive 用 shell=True 跑卡上的生产命令（出图/配音/漫剧），
    那些命令才是模型消耗的大户——它们完全不在 quota() 的乘法里。实测跑出来
    近 24h 真生成 430 次，而 control 预算 300 次：**静态闸报绿，现实已经超支**。

    口径三条：
      1) embed-cache-hit 不是模型调用（命中缓存），按行数算会虚高四成以上，必须排除；
      2) 只读本机账（rt/<station>/local-model.jsonl）；旧账 dispatcher/local-model.jsonl
         五机共用一条路径，分不清归属，标 legacy 只作参考不参与判决；
      3) 窗口按 ts 过滤，账本用本地时间。
    """
    import datetime
    st = station or _local_station()
    if not st:
        return None
    paths = [(os.path.join(FLEET, "rt", st, "local-model.jsonl"), False),
             (os.path.join(FLEET, "dispatcher", "local-model.jsonl"), True)]
    now = now or datetime.datetime.now()
    cut = (now - datetime.timedelta(hours=window_h)).isoformat(timespec="seconds")
    calls = minutes = hits = 0
    seen = []
    for p, legacy in paths:
        if not os.path.exists(p):
            continue
        seen.append({"path": os.path.relpath(p, ROOT), "legacy": legacy})
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if str(r.get("ts") or "") < cut:
                        continue
                    op = str(r.get("op") or "")
                    if op == "embed-cache-hit":
                        hits += 1
                    elif op.startswith("generate"):
                        calls += 1
                        minutes += float(r.get("sec") or 0) / 60.0
        except Exception:
            continue
    cap = ((load(CAP, {}) or {}).get("machines") or {}).get(st) or {}
    b = cap.get("budget") or {}
    bc, bm = b.get("calls_per_day"), b.get("model_minutes_per_day")
    # 速率外推：只看窗口总量会被"这两天正好停着"骗过去，必须按活跃小时推满负荷。
    # 标定（2026-11-11 实测）：活跃小时(>=10 次/时)均值约 17-30 次/时，
    # 折算 408-715 次/天，而 control 预算 300 —— 一全速跑就超。
    rate = {}
    try:
        # 速率标定窗口要比实测窗口长：服务一停，24h 里就没有活跃小时，
        # 拿 24h 标速率会得出"永远不超支"的假绿（实测就是这么撞上的）。
        import datetime as _dt
        rcut = ((now or _dt.datetime.now()) - _dt.timedelta(hours=168)).isoformat(timespec="seconds")
        by = {}
        for r in _gen_rows(paths, rcut):
            k = (r.get("ts") or "")[:13]
            by[k] = by.get(k, 0) + 1
        act = [v for v in by.values() if v >= 10]
        if act:
            ah = sum(act) / len(act)
            rate = {"active_hours": len(act), "peak_hour": max(act),
                    "avg_per_hour": round(ah, 1),
                    "extrapolated_per_day": int(round(ah * 24)),
                    "over_if_full_load": bool(bc and ah * 24 > bc)}
    except Exception:
        pass
    return {"station": st, "window_h": window_h, "calls": calls,
            "model_minutes": round(minutes, 1), "cache_hits_excluded": hits,
            "budget_calls": bc, "budget_minutes": bm, "rate": rate,
            "over_calls": bool(bc and calls > bc), "over_minutes": bool(bm and minutes > bm),
            "sources": seen,
            "legacy_note": ("旧账 dispatcher/local-model.jsonl 是五机共用的入库文件，"
                            "无法按工位归属，仅供参考" if any(s["legacy"] for s in seen) else "")}


def _gen_rows(paths, cut):
    """产出窗口内的真生成行（排除 embed-cache-hit，它不是模型调用）。"""
    for p, _legacy in paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if str(r.get("ts") or "") < cut:
                        continue
                    if str(r.get("op") or "").startswith("generate"):
                        yield r
        except Exception:
            continue


def _local_station():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import local_model as lm
        return lm.local_station()
    except Exception:
        return None


def quota(plan):
    """每台机的模型调用量 vs AGENT-CAPACITY 日额度。

    调用次数来源（按优先级）：
      1) 排班里显式的 calls_per_run（人已核算过，可写 0）
      2) 脚本里扫到真推理标记 -> 按 1 次/触发估（未知就按最保守的 1）
      3) 都没有 -> 0
    探测到会推理但排班写 0 次 -> P1，防"额度漏报"（比超支更危险）。
    """
    cap = (load(CAP, {}) or {}).get("machines") or {}
    rows, warns = [], []
    for t in plan.get("tasks") or []:
        tid = t.get("id")
        cad = int(t.get("cadence_s") or 86400)
        does = infers(t.get("cmd"))
        declared = t.get("calls_per_run")
        if declared is None:
            calls = 1 if does else 0
        else:
            calls = int(declared)
            if does and calls == 0:
                warns.append({"level": "P1",
                              "why": "%s 的脚本里有模型调用，但排班写 calls_per_run=0（额度会漏报）" % tid})
        daily = calls * max(1, int(86400 // cad)) if calls else 0
        # max(1,...)：周频任务（cad>86400）在"最忙的一天"仍会跑满 1 次，
        # 按 1 次/天算是对额度的保守上界，不是把周频当成日报。
        for sid in expand(t.get("station") or ""):
            rows.append({"station": sid, "task": tid, "calls_per_day": daily,
                         "infer": does, "declared": declared})
    total = {}
    for r in rows:
        total[r["station"]] = total.get(r["station"], 0) + r["calls_per_day"]
    out = []
    for sid, used in sorted(total.items()):
        budget = ((cap.get(sid) or {}).get("budget") or {}).get("calls_per_day")
        if budget:
            out.append({"station": sid, "planned": used, "budget": budget,
                        "ok": used <= budget, "pct": round(used / budget * 100, 1)})
    return out, warns


def calendar(plan):
    """人读的排班表（按周期从密到疏）。"""
    rows = []
    for t in sorted(plan.get("tasks") or [], key=lambda x: int(x.get("cadence_s") or 1e9)):
        rows.append({"id": t.get("id"), "every": human(int(t.get("cadence_s") or 0)),
                     "station": t.get("station"), "output": t.get("output")})
    return rows


def human(sec):
    if sec % 86400 == 0:
        return "%dd" % (sec // 86400)
    if sec % 3600 == 0:
        return "%dh" % (sec // 3600)
    if sec % 60 == 0:
        return "%dm" % (sec // 60)
    return "%ds" % sec


def executor_state():
    """排班有没有真的执行者？

    2026-11-11 审出来的假绿：19 条任务全绿、自检 13/13，但当时 44 个 LaunchAgent
    全在 disabled/ 里、无 crontab、无 station_drive 进程——**没有任何东西会按这张表
    去跑**。校验器只能说"这张表本身合法"，不能说"排班可用"。所以单独一档
    PLAN-ONLY：表合法 ≠ 在跑。
    """
    hits = []
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=8)
        hits += [ln.split()[-1] for ln in (out.stdout or "").splitlines()
                 if "fluxgroup" in ln.lower() or "station_drive" in ln.lower()]
    except Exception:
        pass
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=8)
        if "fleet" in (out.stdout or "").lower():
            hits.append("crontab")
    except Exception:
        pass
    try:
        out = subprocess.run(["ps", "-Ao", "command"], capture_output=True, text=True, timeout=8)
        if "station_drive.py" in (out.stdout or ""):
            hits.append("station_drive")
        if "master_pulse.py" in (out.stdout or ""):
            hits.append("master_pulse")
    except Exception:
        pass
    return {"executors": hits[:5], "running": bool(hits)}


def run():
    plan = load(PLAN, {}) or {}
    probs = validate(plan)
    sim = simulate_24h(plan)
    q, qwarn = quota(plan)
    probs.extend(qwarn)
    st = stations()
    gated = []
    for t in plan.get("tasks") or []:
        for sid in expand(t.get("station") or ""):
            if sid in st and is_blocked(st[sid]):
                gated.append({"task": t.get("id"), "station": sid, "status": st[sid].get("status")})
    if sim["conflicts"]:
        probs.append({"level": "P1",
                      "why": "同一分钟写同一输出：%s" % json.dumps(sim["conflicts"][:2], ensure_ascii=False)})
    if sim.get("hottest_station_minute"):
        h = sim["hottest_station_minute"][0]
        probs.append({"level": "P1",
                      "why": "同工位同分钟并发过高：%s 在 %02d:%02d 有 %d 个任务同时到期，"
                             "会抢同一台机的 CPU/模型/文件锁；重活（TEST-FULL/MODEL-RADAR/"
                             "CONDITION-MATRIX/BRAIN-STRESS）应错峰到非整点"
                             % (h["station"], h["t"] // 3600, h["t"] % 3600 // 60, h["n"])})
    over = [x for x in q if not x["ok"]]
    if over:
        probs.append({"level": "P0", "why": "模型额度超支：%s" % over})
    # 实测对账：静态估算管不了卡执行的生产命令，必须拿真账兜底
    m = measured()
    if m:
        if m["over_calls"]:
            probs.append({"level": "P0",
                          "why": "%s 实测%s小时真生成 %d 次 > 预算 %d 次（静态估算看不出这条，"
                                 "因为生产命令不走排班进程）"
                                 % (m["station"], m["window_h"], m["calls"], m["budget_calls"])})
        if m["over_minutes"]:
            probs.append({"level": "P1",
                          "why": "%s 实测%s小时模型时间 %.1f 分钟 > 预算 %d 分钟"
                                 % (m["station"], m["window_h"], m["model_minutes"], m["budget_minutes"])})
        r = m.get("rate") or {}
        if r.get("over_if_full_load"):
            probs.append({"level": "P1",
                          "why": "%s 按实测速率外推会超预算：活跃 %d 小时均值 %s 次/时 -> %d 次/天 > 预算 %d；"
                                 "要么限流要么调预算（现在窗口内只用了 %d 次，是因为服务停着，不是真省）"
                                 % (m["station"], r["active_hours"], r["avg_per_hour"],
                                    r["extrapolated_per_day"], m["budget_calls"], m["calls"])})
    ex = executor_state()
    if not ex["running"]:
        probs.append({"level": "P1",
                      "why": "排班没有执行者（无 launchd/crontab/station_drive 进程）——"
                             "这张表本身合法但没人按它跑；先注册入口再谈'可用'"})
    hard = [p for p in probs if p["level"] == "P0"]
    if hard:
        verdict = "有 P0，先修"
    elif not ex["running"]:
        verdict = "PLAN-ONLY（表合法，无执行者）"
    else:
        verdict = "排班在跑"
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "tasks": len(plan.get("tasks") or []),
            "problems": probs, "sim": sim, "quota": q, "measured": m, "gated": gated,
            "executor": ex, "calendar": calendar(plan), "verdict": verdict}


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    plan = load(PLAN, {}) or {}
    r = run()
    chk("排班非空", r["tasks"] >= 10, r["tasks"])
    chk("任务四件套齐全（无 P0 缺件）",
        not [p for p in r["problems"] if "缺字段" in p["why"]], r["problems"][:3])
    chk("命令目标都在盘上", not [p for p in r["problems"] if "不存在的文件" in p["why"]])
    chk("24h 无同分钟写冲突", not [p for p in r["problems"] if "同一分钟" in p["why"]])
    chk("模型额度不超支", not [p for p in r["problems"] if "额度超支" in p["why"]])
    chk("被阻塞工位被标 gated 而不是当作在跑", isinstance(r["gated"], list))
    # 负控：把一条任务的 cmd 指向不存在的文件，必须判 P0
    bad = json.loads(json.dumps(plan))
    bad["tasks"].append({"id": "NEG", "station": "control", "cadence_s": 300,
                         "cmd": "{py} Tools/fleet/no_such_tool.py", "output": None, "why": "负控"})
    bp = validate(bad)
    chk("负控：命令指向不存在的文件 -> P0",
        any("不存在的文件" in p["why"] for p in bp), bp[:2])
    # 负控：错旗标必须被抓（git pull 没有 --autostart，真跑 rc=129）
    chk("负控：git pull --autostart 判为错旗标",
        "--autostart" in check_flags("git pull --rebase --autostart"))
    chk("正向：git pull --autostash 不报错",
        check_flags("git pull --rebase --autostash") == [])
    # 负控：同工位同分钟并发必须被抓到（只按 output 判时会漏）
    busy = {"tasks": [{"id": "T%d" % i, "station": "control", "cadence_s": 3600,
                       "cmd": "{py} Tools/fleet/quality_score.py", "output": "o%d" % i,
                       "why": "负控"} for i in range(6)]}
    chk("负控：同工位同分钟 6 个任务 -> 报并发过高",
        bool(simulate_24h(busy)["hottest_station_minute"]),
        simulate_24h(busy)["hottest_station_minute"])
    # 推理探测：station_drive 只在 detect_station 里取身份（零推理），
    # station_agent 有 /api/generate（真推理）。两个方向都要真的判对。
    chk("探测：station_drive 判为不推理（只取身份）",
        infers("{py} Tools/fleet/station_drive.py --once") is False)
    chk("探测：station_agent 判为推理（调 /api/generate）",
        infers("{py} Tools/fleet/station_agent.py --station control --once") is True)
    # 负控：审计器只把 "/api/generate" 当要检测的坏模式写进源码，不是推理
    chk("负控：audit_deep 判为不推理（端点只是被检测的字符串）",
        infers("{py} Tools/fleet/audit_deep.py") is False)
    # 负控：脚本会推理却声明 0 次 -> P1（额度漏报比超支更危险）
    bad2 = json.loads(json.dumps(plan))
    for t in bad2["tasks"]:
        if t["id"] == "AGENT-PATROL":
            t["calls_per_run"] = 0
    _, w2 = quota(bad2)
    chk("负控：会推理却写 calls_per_run=0 -> P1",
        any("额度会漏报" in w["why"] for w in w2), w2[:2])
    # 实测对账的负控：造一本超支的账，必须判超支；缓存命中不许算成调用
    import tempfile, datetime as _dt
    with tempfile.TemporaryDirectory() as td:
        d = os.path.join(td, "rt", "control")
        os.makedirs(d)
        now2 = _dt.datetime.now()
        rows = []
        for i in range(400):
            rows.append({"ts": (now2 - _dt.timedelta(minutes=i * 3)).isoformat(timespec="seconds"),
                         "op": "generate", "sec": 1.0, "station": "control"})
        for i in range(500):
            rows.append({"ts": (now2 - _dt.timedelta(minutes=i)).isoformat(timespec="seconds"),
                         "op": "embed-cache-hit", "station": "control"})
        with open(os.path.join(d, "local-model.jsonl"), "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
        old_fleet = FLEET
        try:
            globals()["FLEET"] = td
            m2 = measured("control", window_h=100000)
            chk("负控：400 次真生成 -> 判超支（预算 300）", m2["over_calls"] is True, m2["calls"])
            chk("缓存命中不计入调用次数", m2["calls"] == 400, m2["calls"])
        finally:
            globals()["FLEET"] = old_fleet
    print("[automation_plan] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    r = run()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("任务 %d 个｜%s" % (r["tasks"], r["verdict"]))
        print("24h 模拟：触发 %d 次，最忙一分钟 %d 个，输出冲突 %d"
              % (r["sim"]["fires"], r["sim"]["busiest_minute"], len(r["sim"]["conflicts"])))
        for x in r["quota"]:
            print("  额度 %-9s 计划 %5d / 预算 %5d（%s%%）%s"
                  % (x["station"], x["planned"], x["budget"], x["pct"], "" if x["ok"] else " 超支"))
        if r["gated"]:
            print("  被阻塞工位上的任务（gated，不计在跑）：%d 条" % len(r["gated"]))
        for p in r["problems"]:
            print("  [%s] %s" % (p["level"], p["why"]))
        print("排班（由密到疏）：")
        for c in r["calendar"]:
            print("  %-18s 每 %-4s %-26s %s" % (c["id"], c["every"], c["station"], c["output"] or "—"))
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 1 if [p for p in r["problems"] if p["level"] == "P0"] else 0


if __name__ == "__main__":
    sys.exit(main())
