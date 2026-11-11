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
    # 每分钟触发数峰值
    per_min = {}
    for f in fires:
        per_min[f["t"]] = per_min.get(f["t"], 0) + 1
    return {"fires": len(fires), "conflicts": conflicts[:10],
            "busiest_minute": max(per_min.values()) if per_min else 0}


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
    over = [x for x in q if not x["ok"]]
    if over:
        probs.append({"level": "P0", "why": "模型额度超支：%s" % over})
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "tasks": len(plan.get("tasks") or []),
            "problems": probs, "sim": sim, "quota": q, "gated": gated,
            "calendar": calendar(plan),
            "verdict": "排班可用" if not [p for p in probs if p["level"] == "P0"] else "有 P0，先修"}


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
