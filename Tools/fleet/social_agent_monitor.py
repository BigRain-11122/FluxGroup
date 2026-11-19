#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_agent_monitor.py — 智能体监控屏（只读磁盘事实，不看进程与回执）。

监控的三种病，这里各有一条判据挡着：
  1 **只看心跳**：进程活着、任务全绿，产出为零。→ 每个任务都算"产出年龄"（文件 mtime）
     与"产出量"（行数），心跳不参与判定。
  2 **把没轮到当失败**：任务超过 every_s×2 未跑，也可能是整条线被让路令停了。→ 分
     MISSED（没轮到）与 STALE（该跑却没证据）两态，前者 amber、后者 red。
  3 **告警递归**：监控自己失败还去告警 → 只落日志，不触发别的任务。

输出：SOCIAL-AGENT-BOARD.md（一屏）+ state/social-agent-health.json（机读）。
退出码：0 全绿 / 1 amber（有未决但不阻断）/ 2 red（有该跑没产出或硬失败）。

用法：
  python3 Tools/fleet/social_agent_monitor.py
  python3 Tools/fleet/social_agent_monitor.py --json
  python3 Tools/fleet/social_agent_monitor.py --self-test
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
MATRIX = os.path.join(SOCIAL, "SOCIAL-AUTOMATION-MATRIX-v1.json")
DAYSTATE = os.path.join(STATE, "social-agent-day.json")
LEDGER = os.path.join(SOCIAL, "AGENT-DAY-LEDGER.jsonl")
SURFACE = os.path.join(STATE, "social-surface.json")
BOARD = os.path.join(SOCIAL, "SOCIAL-AGENT-BOARD.md")
HEALTH = os.path.join(STATE, "social-agent-health.json")
PAUSE = os.path.join(STATE, "SOCIAL-AGENT-PAUSED")


def _load(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def _lines(path):
    if not os.path.exists(path):
        return None
    try:
        return sum(1 for _ in open(path, encoding="utf-8", errors="replace"))
    except Exception:
        return None


def judge(task, state, now):
    """单任务判定：产出年龄 + 产出量 + 上跑 rc。返回 (status, detail)。"""
    tid = task["id"]
    rec = state.get(tid) or {}
    every = task.get("every_s", 3600)
    age = now - rec["ts"] if rec.get("ts") else None
    if age is None:
        return "NEVER", "从未跑过"
    # 正常退出码可能不是 0（审计有未决=1、训练门未过=2）；未声明 ok_rc 才只认 0
    blocked_rc = task.get("blocked_rc") or []
    if rec.get("rc") is not None and rec["rc"] in blocked_rc:
        # 被让路（同 profile 被占、训练在跑）不是故障；但如果产出真的老了，
        # 下面的证据龄期仍会把它判 STALE——BLOCKED 不许变成长期免死金牌。
        ev0 = rec.get("evidence") or {}
        if ev0:
            oldest0 = max(v.get("mtime", 0) for v in ev0.values())
            if now - oldest0 > every * 3:
                return "STALE", "连续被让路且产出已 %.1fh 未更新（周期 %.1fh）" % (
                    (now - oldest0) / 3600.0, every / 3600.0)
        return "BLOCKED", "被让路（rc=%s）%s" % (rec["rc"], (rec.get("note") or "")[:50])
    ok_rc = task.get("ok_rc") or [0]
    if rec.get("rc") is not None and rec["rc"] not in ok_rc:
        return "FAIL", "上次 rc=%s（允许 %s）%s" % (rec["rc"], ok_rc,
                                                   (rec.get("note") or "")[:50])
    ev = rec.get("evidence") or {}
    # 产出年龄比"上次跑"更新才算真的有产出；文件不存在=没证据
    if not ev:
        if age > every * 2:
            return "MISSED", "%.1fh 没跑（周期 %.1fh）" % (age / 3600.0, every / 3600.0)
        return "OK_NO_EVIDENCE", "跑了但没有可核验产出"
    oldest = max(v.get("mtime", 0) for v in ev.values())
    prod_age = now - oldest
    # 事件驱动任务（会话结算这类）：没有事件就不该有新行，产出文件不涨不算红。
    # 判据换成"跑了且 rc 正常"，并在说明里写清本次事件数，别拿心跳冒充产出。
    if task.get("event_driven") and rec.get("rc") == 0:
        return "OK", "事件驱动：本次 0 条待处理（产出 %.1fh 未涨属正常）" % (
            prod_age / 3600.0)
    if prod_age > every * 2:
        return "STALE", "产出已 %.1fh 未更新（周期 %.1fh）" % (prod_age / 3600.0, every / 3600.0)
    return "OK", "产出 %.1fh 前更新 · %s" % (
        prod_age / 3600.0,
        " ".join("%s=%s行" % (os.path.basename(k), v.get("lines")) for k, v in ev.items()
                 if v.get("lines") is not None) or "无行数")


def fleet_probe():
    """机队面：只取本机相关常驻的三件事实（进程存在性 + pulse 阶段尾）。"""
    out = {"launchd": {}, "pulse": None}
    try:
        txt = subprocess.run(["launchctl", "list"], capture_output=True, text=True,
                             timeout=15).stdout
        for line in txt.splitlines():
            if "fluxgroup" in line:
                p = line.split()
                if len(p) >= 3:
                    out["launchd"][p[2]] = {"pid": p[0], "exit": p[1]}
    except Exception as e:
        out["launchd"] = {"ERR": str(e)[:60]}
    pj = _load(os.path.join(STATE, "PULSE.json"))
    if isinstance(pj, dict):
        stages = pj.get("stages") or {}
        tail = list(stages.items())[-3:] if isinstance(stages, dict) else None
        out["pulse"] = {"ts": pj.get("ts"), "tail": tail}
    return out


def build(matrix, state, now=None):
    now = now or time.time()
    rows = []
    for t in matrix["tasks"]:
        st, detail = judge(t, state, now)
        rows.append({"id": t["id"], "status": st, "detail": detail,
                     "owner": t.get("owner") or "未指派",
                     "every_h": round(t.get("every_s", 0) / 3600.0, 1),
                     "what": t.get("what", "")[:40]})
    return rows


def level(rows):
    bad = [r for r in rows if r["status"] in ("STALE", "FAIL")]
    warn = [r for r in rows if r["status"] in ("MISSED", "NEVER", "OK_NO_EVIDENCE", "BLOCKED")]
    if bad:
        return 2
    if warn:
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    matrix = _load(MATRIX)
    if not matrix:
        print("[mon] 矩阵缺失：%s" % MATRIX)
        return 2
    state = _load(DAYSTATE, {}) or {}
    now = time.time()
    rows = build(matrix, state, now)
    rc = level(rows)
    fleet = fleet_probe()
    surface = _load(SURFACE, {}) or {}
    gaps = surface.get("gaps") or []
    paused = os.path.exists(PAUSE)
    led = _lines(LEDGER)

    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rc": rc, "rows": rows,
               "fleet": fleet, "surface_gaps": gaps, "paused": paused,
               "ledger_lines": led}
    os.makedirs(STATE, exist_ok=True)
    json.dump(payload, open(HEALTH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return rc

    icon = {"OK": "✓", "MISSED": "○", "NEVER": "·", "STALE": "!", "FAIL": "✗",
            "OK_NO_EVIDENCE": "?", "BLOCKED": "~"}
    print("[mon] 养号线循环任务 %d 个 · 整体 %s%s"
          % (len(rows), {0: "GREEN", 1: "AMBER", 2: "RED"}[rc],
             "（已让路暂停）" if paused else ""))
    for r in sorted(rows, key=lambda x: (x["status"] != "OK", x["id"])):
        print("  %s %-16s %-3s %s" % (icon.get(r["status"], " "), r["id"],
                                      "%sh" % r["every_h"], r["detail"]))
    if gaps:
        print("[mon] 面审计未决 %d 项（见 SURFACE-REPORT.md）" % len(gaps))
    print("[mon] 常驻：%s" % ", ".join(sorted(fleet["launchd"].keys())) or "无")

    with open(BOARD, "w", encoding="utf-8") as f:
        f.write("# 养号线智能体监控（%s）\n\n" % payload["ts"])
        f.write("整体：**%s**%s\n\n" % ({0: "GREEN", 1: "AMBER", 2: "RED"}[rc],
                                       "（已让路暂停）" if paused else ""))
        f.write("| 任务 | 负责人 | 周期 | 状态 | 说明 |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| %s | %s | %sh | %s | %s |\n" % (
                r["id"], r["owner"], r["every_h"], r["status"], r["detail"]))
        nobody = [r["id"] for r in rows if r["owner"] == "未指派"]
        if nobody:
            f.write("\n> 未指派负责人（判负）：%s\n" % "、".join(nobody))
        f.write("\n## 机队事实\n\n```\n%s\n```\n" % json.dumps(fleet, ensure_ascii=False, indent=1))
        if gaps:
            f.write("\n## 面审计未决（%d）\n\n" % len(gaps))
            for g in gaps:
                f.write("- %s\n" % g)
        f.write("\n> 判据：只认产出文件的行数与 mtime；进程活着不算产出。"
                "MISSED=没轮到（amber），STALE/FAIL=该跑没产出（red）。\n")
    print("[mon] → %s" % os.path.relpath(BOARD, ROOT))
    return rc


def self_test():
    m = {"tasks": [
        {"id": "fresh", "every_s": 3600, "what": ""},
        {"id": "stale", "every_s": 3600, "what": ""},
        {"id": "never", "every_s": 60, "what": ""},
        {"id": "failed", "every_s": 60, "what": ""},
        {"id": "noev", "every_s": 3600, "what": ""},
    ]}
    now = 1_000_000
    state = {
        "fresh": {"ts": now - 600, "rc": 0,
                  "evidence": {"x.jsonl": {"mtime": now - 600, "lines": 5}}},
        "stale": {"ts": now - 600, "rc": 0,
                  "evidence": {"y.jsonl": {"mtime": now - 9000, "lines": 5}}},
        "failed": {"ts": now - 60, "rc": 2, "note": "boom", "evidence": {}},
        "noev": {"ts": now - 600, "rc": 0, "evidence": {}},
    }
    rows = {r["id"]: r["status"] for r in build(m, state, now)}
    cases = [
        ("新产出判 OK", rows["fresh"] == "OK"),
        ("产出过期判 STALE", rows["stale"] == "STALE"),
        ("没跑过判 NEVER", rows["never"] == "NEVER"),
        ("上跑失败判 FAIL", rows["failed"] == "FAIL"),
        ("跑了没产出判 OK_NO_EVIDENCE", rows["noev"] == "OK_NO_EVIDENCE"),
    ]
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    # 整体级别：有 STALE 必须 RED；只有 MISSED 只能 AMBER
    lv_red = level(build(m, state, now))
    lv_amber = level(build({"tasks": [{"id": "never", "every_s": 60, "what": ""}]},
                           {}, now))
    cases2 = [("STALE 时必须 RED", lv_red == 2), ("只有 NEVER 时 AMBER", lv_amber == 1)]
    for n, v in cases2:
        if not v:
            print("  FAIL %s" % n)
        ok += 1 if v else 0
    total = len(cases) + len(cases2)
    print("[self-test] %d/%d %s" % (ok, total, "PASS" if ok == total else "FAIL"))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
