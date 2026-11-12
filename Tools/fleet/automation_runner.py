#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""automation_runner.py - 按 AUTOMATION-v1.json 的排班真正执行任务。

2026-11-12 立（批次6 落地）。缺口：排班表有 19 条，但之前只有 SELF-DRIVE 有执行体
（launchd 每 5 分钟跑一次 station_drive --once），其余 18 条（全量测试、审计、评分、
环境探针、文档生成、模型雷达……）从来没有被执行过 —— 表是纸，`automation_plan.py`
只能校验"表合法"，判不出"有没有人按表跑"。

本调度器做三件事：
  1) 读排班 + 上次运行时间，算出哪些到期（due）；
  2) 串行执行（同一时刻只跑一个，避免抢 CPU/模型/文件锁）；
  3) 记录结果与下次到期时间，写 state/automation-run.json + 每日 log。

纪律：
  - **串行**：不并发跑两条（排班里已按"同工位同分钟并发过高"提示过）。
  - **单例**：同一台机同时只允许一个调度器（/tmp 锁）。
  - **不伪造**：命令失败就记失败，不改排班表、不写"已跑"。
  - **gated 跳过**：被阻塞工位（offline/not_installed/blocked_*）上的任务不跑。
  - **不跑自己**：本调度器不把 AUTOMATION-RUNNER 写进排班，避免递归。

用法：
  python3 Tools/fleet/automation_runner.py                 # 跑一轮到期任务
  python3 Tools/fleet/automation_runner.py --dry            # 只列到期，不执行
  python3 Tools/fleet/automation_runner.py --only SELF-DRIVE
  python3 Tools/fleet/automation_runner.py --force TASK     # 忽略到期时间强跑一条
  python3 Tools/fleet/automation_runner.py --self-test
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
PLAN = os.path.join(FLEET, "AUTOMATION-v1.json")
STATE = os.path.join(FLEET, "state")
RUNS = os.path.join(STATE, "automation-run.json")
LOG = os.path.join(STATE, "automation-run.jsonl")
STATIONS_JSON = os.path.join(FLEET, "STATIONS.json")
BLOCKED_PREFIX = ("offline", "not_installed", "blocked")


def load(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def stations():
    return {s["id"]: s for s in (load(STATIONS_JSON, {}) or {}).get("stations") or []}


def my_station():
    try:
        sys.path.insert(0, HERE)
        import fleet_identity as fid
        return fid.station_or_none()
    except Exception:
        return None


def expand(field):
    st = list(stations())
    if field == "all":
        return st
    if "|" in str(field):
        return [x.strip() for x in str(field).split("|") if x.strip()]
    return [field]


def cmd_for(task, station):
    """把 {py} 与 <station> 占位替换成本机实际值。"""
    cmd = str(task.get("cmd") or "")
    py = "python" if os.name == "nt" else "python3"
    cmd = cmd.replace("{py}", py).replace("<station>", station or "control")
    return cmd


def due_tasks(plan, runs, station, now=None):
    """返回 (到期任务列表, 跳过说明)。"""
    now = now or time.time()
    out, skipped = [], []
    st = stations()
    for t in plan.get("tasks") or []:
        tid = t.get("id")
        cad = int(t.get("cadence_s") or 0)
        if not tid or cad <= 0:
            continue
        mine = station in expand(t.get("station") or "")
        if not mine:
            continue
        # 只在**本机**被阻塞时跳过（station: all 的任务不该因为别的机器离线就整条不跑）。
        me_status = str((st.get(station) or {}).get("status") or "")
        if me_status.startswith(BLOCKED_PREFIX) and not t.get("allow_blocked"):
            skipped.append({"task": tid, "why": "本机状态=%s，不自驱" % me_status})
            continue
        last = float((runs.get(tid) or {}).get("last") or 0)
        if now - last >= cad:
            out.append(t)
    out.sort(key=lambda x: float((runs.get(x["id"]) or {}).get("last") or 0))
    return out, skipped


def run_one(task, station, timeout=1800):
    cmd = cmd_for(task, station)
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        rc, out = p.returncode, ((p.stdout or "") + (p.stderr or ""))
    except subprocess.TimeoutExpired:
        rc, out = -9, "TIMEOUT after %ss" % timeout
    except Exception as e:
        rc, out = -1, "EXEC-ERROR: %s" % e
    return {"id": task.get("id"), "rc": rc, "sec": round(time.time() - t0, 1),
            "tail": out.strip().splitlines()[-3:] if out.strip() else []}


def singleton():
    """同机只允许一个调度器同时跑。返回句柄或 None。"""
    import tempfile as tf
    p = os.path.join(tf.gettempdir(), "fluxgroup-automation-runner.lock")
    try:
        fh = open(p, "a+")
    except Exception:
        return None
    try:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except ImportError:
        try:
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return fh
        except Exception:
            fh.close()
            return None
    except Exception:
        fh.close()
        return None


def run(dry=False, only=None, force=None):
    plan = load(PLAN, {}) or {}
    station = my_station()
    if not station:
        return {"error": "无法判定本机工位", "rc": 2}
    runs = load(RUNS, {}) or {}
    if force:
        cand = [t for t in plan.get("tasks") or [] if t.get("id") == force]
        due, skipped = cand, []
    elif only:
        cand = [t for t in plan.get("tasks") or [] if t.get("id") == only]
        due, skipped = cand, []
    else:
        due, skipped = due_tasks(plan, runs, station)

    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "station": station,
              "due": [t.get("id") for t in due], "skipped": skipped, "ran": [],
              "dry": bool(dry)}
    if dry:
        return report

    lock = singleton()
    if lock is None:
        report["error"] = "已有调度器在跑（单例锁被占用）"
        return report

    results = []
    for t in due:                      # 串行：一条跑完再下一条
        r = run_one(t, station)
        results.append(r)
        runs[t["id"]] = {"last": time.time(), "rc": r["rc"], "sec": r["sec"]}
        report["ran"].append(r)
        try:
            os.makedirs(STATE, exist_ok=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(dict(r, ts=report["ts"], station=station),
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(RUNS, "w", encoding="utf-8") as f:
            json.dump(runs, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return report


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    plan = load(PLAN, {}) or {}
    chk("排班可读且非空", len(plan.get("tasks") or []) >= 10, len(plan.get("tasks") or []))
    st = my_station()
    chk("本机工位可判定", bool(st), st)

    # 到期判定：从没跑过的任务必须到期
    due, _ = due_tasks(plan, {}, st or "control")
    chk("从没跑过 -> 全部到期", len(due) >= 10, len(due))

    # 负控：刚跑过 1 秒的 5 分钟周期任务不该再到期
    runs = {t["id"]: {"last": time.time() - 1} for t in (plan.get("tasks") or [])}
    due2, _ = due_tasks(plan, runs, st or "control")
    chk("负控：刚跑过 -> 不到期", len(due2) == 0, [t["id"] for t in due2][:3])

    # 占位替换
    fake = {"cmd": "{py} Tools/fleet/x.py --station <station>"}
    c = cmd_for(fake, "visual")
    chk("{py}/<station> 占位被替换", "<station>" not in c and "{py}" not in c and "visual" in c, c)

    # 负控：被阻塞工位上的任务必须跳过
    blocked = [k for k, v in stations().items() if str(v.get("status") or "").startswith(BLOCKED_PREFIX)]
    if blocked:
        bp = {"tasks": [{"id": "B1", "station": blocked[0], "cadence_s": 60,
                         "cmd": "{py} -c pass", "why": "负控"}]}
        d, sk = due_tasks(bp, {}, blocked[0])
        chk("负控：本机被阻塞时任务跳过并说明", not d and sk and "不自驱" in sk[0]["why"], (d, sk))
    else:
        chk("负控：当前无阻塞工位（跳过此项）", True)

    # 失败要如实记录
    r = run_one({"id": "FAILCASE", "cmd": "%s -c \"import sys;sys.exit(7)\"" %
                 ("python" if os.name == "nt" else "python3")}, st or "control", timeout=30)
    chk("命令失败 rc 如实记录", r["rc"] == 7, r["rc"])
    print("[automation_runner] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--force", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    r = run(dry=a.dry, only=a.only, force=a.force)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        if r.get("error"):
            print("错误：%s" % r["error"])
            return 2
        print("工位 %s｜到期 %d 条｜跳过 %d 条%s"
              % (r["station"], len(r["due"]), len(r["skipped"]), "（演练）" if a.dry else ""))
        for x in r["ran"]:
            print("  %-22s rc=%-4s %5.1fs" % (x["id"], x["rc"], x["sec"]))
        for s in r["skipped"]:
            print("  跳过 %-18s %s" % (s["task"], s["why"]))
    return 0 if all(x["rc"] == 0 for x in r.get("ran") or []) else 1


if __name__ == "__main__":
    sys.exit(main())
